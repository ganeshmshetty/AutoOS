"""
planner.py — Rich intent classification for AutoOS Gateway.

Returns a fully structured TaskPlan so executors receive zero-ambiguity
parameters — no raw string parsing happens downstream.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from server.agent.bus import emit_event
from server.agent.llm_factory import get_llm, invoke_with_fallback
from server.agent.state import AgentState

logger = logging.getLogger("AutoOS.planner")


# ── Structured output schema ──────────────────────────────────────────────────

class TaskPlan(BaseModel):
    category: Literal["browser", "os", "ambiguous"] = Field(
        description="Top-level route: 'browser' needs the web, 'os' is local."
    )
    sub_category: Literal[
        "web_search", "web_form", "media_playback", "gov_portal",
        "file_ops", "app_launch", "hardware", "settings",
        "process_mgmt", "security", "diagnostics", "unknown",
    ] = Field(description="The specific intent within the chosen category.")
    plain_english_plan: str = Field(
        description=(
            "One short sentence (max 20 words) describing what will happen. "
            "Zero jargon. Write for someone who is not tech-savvy."
        )
    )
    entities: list[str] = Field(
        default_factory=list,
        description=(
            "Key nouns extracted from the request — app name, file name, "
            "website, setting name, device type. Keep entries short and exact."
        ),
    )
    action_params: dict = Field(
        default_factory=dict,
        description=(
            "Structured parameters for the executor. The schema depends on sub_category:\n"
            "  app_launch   → {app_name: str, search_aliases: list[str]}\n"
            "  file_ops     → {keywords: list[str], file_types: list[str], time_hint: str, action: str}\n"
            "  hardware     → {device_type: str}\n"
            "  settings     → {setting: str, direction: str}\n"
            "  media_playback → {platform: str, content_type: str, query: str}\n"
            "  web_search   → {query: str}\n"
            "  web_form     → {site: str, action: str}\n"
            "  gov_portal   → {portal: str, action: str}\n"
            "  process_mgmt → {action: str, targets: list[str]}\n"
            "  security     → {action: str}\n"
            "  diagnostics  → {check_type: str}"
        ),
    )
    needs_hitl: bool = Field(
        default=False,
        description=(
            "True if the action is IRREVERSIBLE or DESTRUCTIVE — deleting files, "
            "killing a system process, modifying system settings, submitting forms."
        ),
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this classification (0.0-1.0).",
    )


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are the AutoOS Gateway Planner — an intelligent intent classifier for an AI \
desktop assistant. Your ONLY job is to understand the user's natural-language \
request and return a structured TaskPlan JSON. Do NOT execute anything.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CATEGORIES & SUB-CATEGORIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

browser — Requires the internet or a website:
  web_search      → Look up information (Google, Wikipedia, news, weather, stock prices)
  web_form        → Log in, fill or submit a form on a website (email, shopping, booking)
  media_playback  → Play video, music, or podcast from an ONLINE platform (YouTube, Spotify,
                    Netflix, Prime Video, Hotstar, Gaana, JioSaavn)
  gov_portal      → Government websites (DigiLocker, Aadhaar, EPFO, income-tax, IRCTC)

os — Acts on the local Windows PC without needing the internet:
  file_ops        → Find, open, copy, move, delete, rename files or folders
  app_launch      → Start ANY application installed on the PC:
                    - Games: Valorant, GTA, Minecraft, Steam, Epic Games
                    - Office: Word, Excel, PowerPoint, Notepad
                    - Browsers: Chrome, Edge, Firefox (launching only, not navigating)
                    - Media: VLC, Windows Media Player, Spotify (desktop app)
                    - Utilities: Calculator, Paint, Task Manager, Control Panel
                    - Custom/Gaming launchers: Riot Client, Battle.net, Steam, Epic
  hardware        → USB drives, printers, Wi-Fi adapter, Bluetooth, sound, display hardware
  settings        → Brightness, text/font size, contrast, dark mode, accessibility features,
                    screen resolution, magnifier
  process_mgmt    → List, switch to, or forcefully close running programs
  security        → Virus scan, Windows Update, suspicious software, lock screen / PIN
  diagnostics     → Slow PC, crashes, blue screens, Event Log errors, Recycle Bin, disk space

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTELLIGENCE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ALWAYS pick the most specific sub_category — never leave it as 'unknown' if you can infer.
2. app_launch = ANY request to open/run/start/play a locally installed application.
   NEVER route a game, office app, or desktop app to 'browser' or 'web_search'.
3. media_playback is ONLY for streaming from the web (YouTube, Netflix, etc.).
   Playing a local video file → file_ops, opening VLC → app_launch.
4. "Check email" → web_form (Gmail/Outlook web) unless the user says "open Outlook" → app_launch.
5. Ambiguous requests (e.g. "spotify") → prefer app_launch since the desktop app is common.
6. needs_hitl = true for: delete, format, kill system process, OS-level updates,
   submitting government forms, anything irreversible.
7. action_params MUST always be populated with the most specific data you can extract.
   For app_launch, always provide search_aliases including common filename variations.
8. entities must contain the exact name(s) — app name, file name, website, setting, etc.
9. plain_english_plan: one short sentence, no technical words.
10. confidence < 0.7 means the request is genuinely ambiguous.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORKED EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"open valorant"
  category=os, sub_category=app_launch, confidence=0.99
  entities=["Valorant"]
  action_params={"app_name": "Valorant", "search_aliases": ["valorant", "VALORANT", "RiotClientServices", "VALORANT-Win64-Shipping"]}
  plain_english_plan="I will open Valorant on your computer."

"launch gta 5"
  category=os, sub_category=app_launch, confidence=0.98
  entities=["GTA 5"]
  action_params={"app_name": "GTA V", "search_aliases": ["GTA5", "GTAV", "Grand Theft Auto V", "PlayGTAV"]}
  plain_english_plan="I will launch Grand Theft Auto V."

"play a trending video on youtube"
  category=browser, sub_category=media_playback, confidence=0.97
  entities=["YouTube", "trending"]
  action_params={"platform": "YouTube", "content_type": "trending", "query": "trending videos"}
  plain_english_plan="I will open YouTube and play a trending video for you."

"where is my report file"
  category=os, sub_category=file_ops, confidence=0.92
  entities=["report"]
  action_params={"keywords": ["report"], "file_types": [".docx", ".pdf", ".xlsx"], "time_hint": "any", "action": "search"}
  plain_english_plan="I will search your computer for a file called 'report'."

"i cant see my USB"
  category=os, sub_category=hardware, confidence=0.95
  entities=["USB"]
  action_params={"device_type": "usb"}
  plain_english_plan="I will check if any USB drives are connected to your computer."

"make the text bigger"
  category=os, sub_category=settings, confidence=0.98
  entities=["text size"]
  action_params={"setting": "text_size", "direction": "increase"}
  plain_english_plan="I will increase the text size so it is easier to read."

"check if my computer has virus"
  category=os, sub_category=security, confidence=0.96
  entities=["virus scan"]
  action_params={"action": "virus_scan"}
  plain_english_plan="I will run a virus scan using Windows Defender."

"close notepad"
  category=os, sub_category=process_mgmt, confidence=0.97, needs_hitl=true
  entities=["Notepad"]
  action_params={"action": "kill", "targets": ["Notepad", "notepad.exe"]}
  plain_english_plan="I will close the Notepad window."

"open digilocker"
  category=browser, sub_category=gov_portal, confidence=0.94
  entities=["DigiLocker"]
  action_params={"portal": "DigiLocker", "action": "open"}
  plain_english_plan="I will open DigiLocker in your browser."

"my computer is very slow"
  category=os, sub_category=diagnostics, confidence=0.91
  entities=["performance"]
  action_params={"check_type": "performance"}
  plain_english_plan="I will check what is making your computer slow."

"open spotify"
  category=os, sub_category=app_launch, confidence=0.85
  entities=["Spotify"]
  action_params={"app_name": "Spotify", "search_aliases": ["Spotify", "Spotify.exe"]}
  plain_english_plan="I will open Spotify on your computer."

"search for flights to delhi"
  category=browser, sub_category=web_search, confidence=0.93
  entities=["flights", "Delhi"]
  action_params={"query": "flights to Delhi"}
  plain_english_plan="I will search for flights to Delhi online."

"delete old files from downloads"
  category=os, sub_category=file_ops, confidence=0.88, needs_hitl=true
  entities=["Downloads", "old files"]
  action_params={"keywords": [], "file_types": [], "time_hint": "old", "action": "delete", "folder": "downloads"}
  plain_english_plan="I will show you old files in your Downloads folder for deletion."
"""


# ── Planner node ──────────────────────────────────────────────────────────────

async def planner(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Classifies the user task into a rich TaskPlan and stores it in AgentState.
    """
    task = state.get("task", "").strip()
    if not task:
        return {
            "next_action": "end",
            "sub_category": "unknown",
            "entities": [],
            "action_params": {},
            "plain_english_plan": "No task was provided.",
            "confidence": 1.0,
            "needs_hitl": False,
            "result": "No task provided.",
        }

    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(TaskPlan)
    prompt = f'{_SYSTEM_PROMPT}\n\nUser request: "{task}"'

    logger.info("Classifying task: %s", task)
    plan: TaskPlan = await invoke_with_fallback(structured_llm, prompt)
    logger.info(
        "Plan → category=%s sub=%s params=%s hitl=%s",
        plan.category, plan.sub_category, plan.action_params, plan.needs_hitl,
    )

    await emit_event(config, {
        "type": "classification",
        "category": plan.category,
        "sub_category": plan.sub_category,
        "plain_english_plan": plan.plain_english_plan,
        "confidence": plan.confidence,
        "needs_hitl": plan.needs_hitl,
    })

    return {
        "next_action": plan.category,
        "sub_category": plan.sub_category,
        "entities": plan.entities,
        "action_params": plan.action_params,
        "plain_english_plan": plan.plain_english_plan,
        "confidence": plan.confidence,
        "needs_hitl": plan.needs_hitl,
        "messages": [{
            "role": "assistant",
            "content": (
                f"[Planner] {plan.category}/{plan.sub_category} — "
                f"{plan.plain_english_plan}"
            ),
        }],
    }

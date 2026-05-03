"""
whatsapp_module.py — High-intelligence automation for WhatsApp Desktop.
Uses Windows UI Automation (UIA) to read and interact with the app structure.
"""
from __future__ import annotations
import logging
import asyncio
import subprocess
import os
try:
    import uiautomation as auto
    import pyautogui
except ImportError:
    auto = None
    pyautogui = None

logger = logging.getLogger("AutoOS.whatsapp_module")

async def run(task: str, entities: list[str], action_params: dict) -> str:
    if not auto:
        return "WhatsApp automation engine is not installed."

    action = action_params.get("action", "").lower()
    chat_name = action_params.get("target") or (entities[0] if entities else "")
    text = action_params.get("input", "")

    # Ensure WhatsApp is open and focused
    whatsapp = auto.WindowControl(searchDepth=1, Name="WhatsApp")
    if not whatsapp.Exists(0):
        # Try to dynamic launch via PowerShell
        logger.info("WhatsApp not found, attempting dynamic launch...")
        cmd = 'powershell -Command "Get-StartApps *WhatsApp* | Select-Object -ExpandProperty AppID"'
        try:
            appid = subprocess.check_output(cmd, shell=True).decode().strip()
            if appid:
                subprocess.Popen(f"explorer.exe shell:AppsFolder\\{appid}", shell=True)
                await asyncio.sleep(8.0) # WhatsApp takes a while to load
                whatsapp = auto.WindowControl(searchDepth=1, Name="WhatsApp")
            else:
                return "WhatsApp is not installed on this system."
        except:
            return "Failed to discover WhatsApp AppID via PowerShell."
        
        if not whatsapp.Exists(2):
            return "Could not find or open WhatsApp Desktop after launching."

    whatsapp.SetFocus()
    
    if action == "send_message" or (text and chat_name):
        res = await _send_message(whatsapp, chat_name, text)
        if "Sent" in res or "Attempted" in res:
             return f"✓ Message sent successfully to {chat_name}.\n\nText: \"{text}\""
        return res
    
    elif action == "read_messages" or "read" in task.lower():
        res = await _read_messages(whatsapp, chat_name)
        return f"Here are the latest messages in your chat with {chat_name}:\n\n{res}"

    elif action == "open_link" or "link" in task.lower():
        return await _open_links(whatsapp, chat_name)

    return f"I found WhatsApp, but I don't know how to '{action}' yet."


async def _send_message(whatsapp: auto.WindowControl, chat_name: str, text: str) -> str:
    try:
        # 1. Search for the chat
        logger.info(f"Searching for chat: {chat_name}")
        
        # Aggressive Focus
        for _ in range(3):
            whatsapp.SetFocus()
            if whatsapp.HasKeyboardFocus: break
            await asyncio.sleep(0.5)
        
        # If still no focus, try clicking the center
        if not whatsapp.HasKeyboardFocus:
            rect = whatsapp.BoundingRectangle
            pyautogui.click(rect.left + 100, rect.top + 10) # Click title bar area
            await asyncio.sleep(0.5)

        search_box = whatsapp.EditControl(Name="Search or start new chat")
        if not search_box.Exists(0.5):
            # Use Ctrl+F
            pyautogui.hotkey('ctrl', 'f')
            await asyncio.sleep(0.8)
        else:
            search_box.Click()
            await asyncio.sleep(0.5)

        # Type the name slowly
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(chat_name, interval=0.05)
        await asyncio.sleep(2.0) # WAIT for search results to filter
        pyautogui.press('enter')
        await asyncio.sleep(1.5) # WAIT for chat to open

        # 2. Type and send the message
        # We don't necessarily need to find the box if focus is correct
        logger.info("Attempting message delivery...")
        pyautogui.write(text, interval=0.02)
        await asyncio.sleep(0.5)
        pyautogui.press('enter')
        
        return f"Sent message to '{chat_name}': {text}"
    except Exception as e:
        logger.error("WhatsApp send failed: %s", e)
        return f"Failed to send message: {e}"


async def _read_messages(whatsapp: auto.WindowControl, chat_name: str) -> str:
    try:
        # Search for chat if needed
        if chat_name:
            await _send_message(whatsapp, chat_name, "") # Just search and enter

        # Find the message list container
        # The new WhatsApp often has it as a 'Group' or 'List' or 'Pane'
        msg_list = whatsapp.ListControl(searchDepth=10, Name="Message list")
        if not msg_list.Exists(1):
            # Try to find any list that is large
            msg_list = whatsapp.ListControl(searchDepth=10)
        
        if not msg_list.Exists(1):
            # Last resort: Look for the 'WhatsApp - Web content' pane and its children
            web_pane = whatsapp.PaneControl(Name="WhatsApp - Web content")
            if web_pane.Exists(1):
                msg_list = web_pane
            else:
                return "I couldn't find the message list in the current WhatsApp window."

        messages = []
        # Get children and filter for things that look like messages
        # In the webview, message bubbles often have a Name that is the text
        bubbles = msg_list.GetChildren()
        if not bubbles:
            # Try walking deeper
            bubbles = []
            def find_bubbles(c, d):
                if c.Name and len(c.Name) > 1 and c.ControlTypeName in ["TextControl", "ListItemControl", "PaneControl"]:
                    bubbles.append(c)
                return True
            msg_list.WalkControl(find_bubbles, maxDepth=3)

        for bubble in bubbles[-8:]: # Get more context
            txt = bubble.Name
            if txt and len(txt) > 1 and "Type a message" not in txt:
                messages.append(txt)
        
        if not messages:
            return "The chat history appears to be empty or in an unreadable format."
            
        return "\n".join(f"• {m}" for m in messages if m.strip())
    except Exception as e:
        logger.error("WhatsApp read failed: %s", e)
        return f"Failed to read messages: {e}"


async def _open_links(whatsapp: auto.WindowControl, chat_name: str) -> str:
    try:
        if chat_name:
             await _send_message(whatsapp, chat_name, "")

        msg_list = whatsapp.ListControl(Name="Message list")
        bubbles = msg_list.GetChildren()
        
        links_found = []
        for bubble in bubbles[-3:]: # Check last 3 messages
            # Search for Hyperlink controls within the bubble
            links = bubble.GetChildren()
            for l in links:
                if l.ControlTypeName == "Hyperlink":
                    url = l.Name # Often the URL is the name
                    if "http" in url:
                        links_found.append(url)
                        os.startfile(url)
        
        if links_found:
            return f"Found and opened {len(links_found)} link(s): " + ", ".join(links_found)
        return "No links found in the recent messages."
    except Exception as e:
        return f"Failed to open links: {e}"

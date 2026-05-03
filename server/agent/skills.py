import json
from pathlib import Path

def is_skill_enabled(skill_id: str, default: bool = True) -> bool:
    try:
        wf_path = Path("server/knowledge/skills.json")
        if not wf_path.exists():
            return default
        with open(wf_path, "r") as f:
            skills = json.load(f)
            for s in skills:
                if s["id"] == skill_id:
                    return s["enabled"]
    except Exception:
        pass
    return default

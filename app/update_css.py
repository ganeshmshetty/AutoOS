import re

with open("/Users/ganesh/dev/OSauto/app/src/index.css", "r") as f:
    css = f.read()

# Replace colors for light mode
replacements = {
    "#020617": "#f1f5f9", # App bg
    "#050505": "#f8fafc", # Sidebar bg
    "#0f172a": "#ffffff", # Card bg
    "#1e293b": "#e2e8f0", # Borders / user msg
    "#334155": "#cbd5e1", # Sec border
    "#94a3b8": "#475569", # muted text
    "#cbd5e1": "#334155", # text
    "#e2e8f0": "#1e293b", # text
    "#f8fafc": "#0f172a", # Heading text
    "rgba(255,255,255,0.05)": "rgba(0,0,0,0.05)",
    "rgba(255,255,255,0.1)": "rgba(0,0,0,0.1)",
    "rgba(255,255,255,0.02)": "rgba(0,0,0,0.02)",
    "color-scheme: dark;": "color-scheme: light;",
    "rgba(2, 6, 23, 0.85)": "rgba(255, 255, 255, 0.85)", # Modal overlay
    "rgba(2, 6, 23, 0.92)": "rgba(255, 255, 255, 0.92)", # Voice overlay
}

# Specific fix for workflow size
css = css.replace("minmax(340px, 1fr)", "minmax(250px, 1fr)")
css = css.replace("height: 120px;", "height: 80px;")
css = css.replace("gap: 2rem;", "gap: 1.25rem;")
css = css.replace("padding: 2.5rem;", "padding: 1.5rem;")
css = css.replace("padding: 1.5rem;", "padding: 1rem;") # general card padding reduction

# Replace all colors (case insensitive but exact match)
for old, new in replacements.items():
    css = re.sub(re.escape(old), new, css, flags=re.IGNORECASE)

# Fix user message text color (since user bg is #e2e8f0 now, text should be dark)
# We might need to manually ensure contrast. User bg: e2e8f0. Color: #0f172a.
css = css.replace("color: white;", "color: #0f172a;")

with open("/Users/ganesh/dev/OSauto/app/src/index.css", "w") as f:
    f.write(css)

print("CSS updated for light mode and workflow sizes")

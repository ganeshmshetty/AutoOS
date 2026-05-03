# Role 3: OS Intelligence & Personalization

## Objective

Implement high-level assistance, guided setups, and accessibility controls using Python 3.12 and Agent-S.

## Tech Stack

- **Python 3.12**
- **Agent-S** (`gui-agents`)
- **System APIs**: `subprocess`, `winreg`

## Tasks & Requirements

### 1. Guided Setup ("Do it for me")

- **Functionality**: Automate complex setups like WhatsApp Web, DigiLocker, or Govt Portal logins.
- **Agent-S Integration**: Use Agent-S to visually navigate the browser and apps, performing the setup steps on behalf of the user.

### 2. Accessibility Toggles

- **Functionality**: Change font sizes, toggle high contrast mode, and enable the screen magnifier.
- **Agent-S Integration**: Navigate the "Ease of Access" settings visually to ensure changes are applied correctly.

### 3. Reminders & Alerts Service

- **Functionality**: Create a background daemon for medicine reminders, call alerts, and screen time notifications.
- **UI Interaction**: Use Agent-S to show large, readable notification windows.

### 4. App Launcher by Description

- **Functionality**: Launch apps based on plain language descriptions (e.g., "Open the thing for writing letters" -> WordPad).
- **Automation**: Search for and launch executables.

## Rules

- **Safety First**: Never perform irreversible actions (like deleting large folders) without a large, visual confirmation dialog.
- **User Preference**: Learn and store user nicknames for files and apps to personalize interactions.

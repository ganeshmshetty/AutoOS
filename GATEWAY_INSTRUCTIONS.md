# AutoOS Gateway: Setup & Testing Guide

This document provides step-by-step instructions for setting up, running, and testing the Main Gateway of the AutoOS project.

---

## 1. Prerequisites

Before starting, ensure you have the following installed:
- **Python 3.12**
- **Playwright** (for browser automation)
- **A Google Gemini API Key**

---

## 2. Installation

1.  **Activate your Virtual Environment**:
    ```powershell
    # From the project root
    .\.venv\Scripts\Activate.ps1
    ```

2.  **Install the Server Package**:
    ```powershell
    pip install -e server/
    ```

3.  **Install Browser Binaries**:
    ```powershell
    playwright install chromium
    ```

---

## 3. Configuration

Create a `.env` file in the `server/` directory (or copy from `.env.example`).

**[server/.env](file:///c:/Users/jaswa/Downloads/AutoOS/server/.env)**:
```env
AUTOFLOW_PORT=8765
GOOGLE_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-pro
```

---

## 4. Running the Gateway

Start the FastAPI backend server:

```powershell
python server/main.py
```

The server will start at `http://localhost:8765`. You can view the interactive API documentation at `http://localhost:8765/docs`.

---

## 5. Testing the Gateway

There are two ways to test the gateway to ensure the routing and browser automation are working.

### Option A: Using the Test Script
I have provided a helper script to send requests easily:

```powershell
# Default test (SpaceX news)
python scripts/test_gateway.py

# Custom task
python scripts/test_gateway.py "Check the weather in Tokyo"
```

### Option B: Using cURL
You can also test via raw HTTP requests:

```powershell
curl -X POST "http://localhost:8765/execute" `
     -H "Content-Type: application/json" `
     -d '{"task": "Search for the latest NVIDIA stock price"}'
```

---

## 6. How it Works (The Gateway Flow)

The Gateway uses **LangGraph** to process every request through a specific lifecycle:

1.  **Input**: The user speaks or types a task.
2.  **Planner Node**: The task is sent to Gemini to decide if it's a `browser` task or an `os` task.
3.  **Router**: A conditional switch that directs the flow:
    *   If **Browser**: It triggers the `browser_executor` which uses `browser-use` to navigate the web.
    *   If **OS**: It currently flags the request as an OS task (to be handled by Agent-S in the next phase).
4.  **Result**: The final output is returned to the user via the API response.

---

## 7. Troubleshooting

- **API Key Errors**: Ensure your `GOOGLE_API_KEY` is valid and has access to the model specified in `LLM_MODEL`.
- **Browser Failures**: If `browser-use` fails to start, try running `playwright install` again.
- **Port Conflicts**: If port `8765` is in use, change `AUTOFLOW_PORT` in your `.env` file.

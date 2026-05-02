import requests
import json
import sys

def test_gateway(task: str):
    url = "http://localhost:8765/execute"
    payload = {"task": task}
    headers = {"Content-Type": "application/json"}

    print(f"Sending task: {task}")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            print("Response Received:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_task = "Search for the latest news on SpaceX"
    if len(sys.argv) > 1:
        test_task = " ".join(sys.argv[1:])
    test_gateway(test_task)

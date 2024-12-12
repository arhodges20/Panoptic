import psutil
import requests
import time

# Centralized server configuration
SERVER_URL = "http://10.10.50.4:5000/stats"  # Replace with your centralized server's IP and port

def collect_stats():
    """
    Collect system stats such as CPU and memory usage.
    """
    return {
        "cpu": psutil.cpu_percent(interval=1),  # Collect CPU usage over a 1-second interval
        "memory": psutil.virtual_memory().percent  # Collect memory usage percentage
    }

def send_stats():
    """
    Send system stats to the centralized server in a loop.
    """
    while True:
        stats = collect_stats()
        try:
            response = requests.post(SERVER_URL, json=stats)
            if response.status_code == 200:
                print(f"Successfully sent stats: {stats}")
            else:
                print(f"Failed to send stats. Server responded with status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending stats: {e}")
        time.sleep(10)  # Send stats every 10 seconds

if __name__ == "__main__":
    print(f"Starting agent to send stats to {SERVER_URL}")
    send_stats()

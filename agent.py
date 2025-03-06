import psutil
import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Server configuration
SERVER_URL = "http://localhost:5000"

def get_system_stats():
    """Collect system statistics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        return {
            "cpu": cpu_percent,
            "memory": memory_percent
        }
    except Exception as e:
        logging.error(f"Error collecting system stats: {e}")
        return None

def get_new_processes():
    """Get list of new processes started in the last minute."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'create_time']):
            try:
                pinfo = proc.info
                # Check if process was created in the last minute
                if time.time() - pinfo['create_time'] <= 60:
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "user": pinfo['username']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes
    except Exception as e:
        logging.error(f"Error collecting process information: {e}")
        return []

def get_privileged_processes():
    """Get list of processes running with elevated privileges."""
    try:
        privileged = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                pinfo = proc.info
                # On Windows, check for admin processes
                # On Unix-like systems, check for root processes
                if (pinfo['username'] == 'SYSTEM' or 
                    pinfo['username'] == 'root' or 
                    pinfo['username'].endswith('Administrator')):
                    privileged.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "user": pinfo['username']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return privileged
    except Exception as e:
        logging.error(f"Error collecting privileged process information: {e}")
        return []

def send_data_to_server(data):
    """Send collected data to the server."""
    try:
        response = requests.post(f"{SERVER_URL}/api/logs", json=data)
        if response.status_code == 200:
            logging.info("Successfully sent data to server")
        else:
            logging.error(f"Failed to send data to server. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending data to server: {e}")

def main():
    logging.info("Starting Panoptic Agent...")
    
    while True:
        try:
            # Collect all data
            stats = get_system_stats()
            new_procs = get_new_processes()
            priv_procs = get_privileged_processes()

            if stats:
                data = {
                    "cpu": stats["cpu"],
                    "memory": stats["memory"],
                    "new_processes": new_procs,
                    "privileged_processes": priv_procs
                }
                send_data_to_server(data)
            
            # Wait for 10 seconds before next collection
            time.sleep(10)
            
        except KeyboardInterrupt:
            logging.info("Stopping Panoptic Agent...")
            break
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            time.sleep(10)  # Wait before retrying

if __name__ == "__main__":
    main()

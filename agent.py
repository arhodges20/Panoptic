import psutil
import requests
import time
import logging
import platform
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Server configuration
SERVER_URL = "http://192.168.100.4:5000"
logging.info(f"Connecting to server at: {SERVER_URL}")

# OS detection
IS_WINDOWS = platform.system().lower() == 'windows'

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
                    username = pinfo.get('username')
                    if not username:
                        logging.debug(f"Process {pinfo['name']} (PID: {pinfo['pid']}) has no user information")
                        username = "Unknown"
                    
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "user": username
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logging.debug(f"Could not access process information: {e}")
                continue
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
                username = pinfo.get('username')
                if not username:
                    logging.debug(f"Process {pinfo['name']} (PID: {pinfo['pid']}) has no user information")
                    continue
                    
                if IS_WINDOWS:
                    # Windows-specific privileged process detection
                    # Check for various Windows privileged users and groups
                    privileged_users = [
                        'SYSTEM',
                        'Administrator',
                        'Administrators',
                        'NT AUTHORITY\\SYSTEM',
                        'NT AUTHORITY\\LOCAL SERVICE',
                        'NT AUTHORITY\\NETWORK SERVICE'
                    ]
                    
                    # Check if username matches any privileged users
                    if any(priv_user.lower() in username.lower() for priv_user in privileged_users):
                        logging.debug(f"Found privileged process: {pinfo['name']} (PID: {pinfo['pid']}) running as {username}")
                        privileged.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "user": username
                        })
                else:
                    # Unix-like systems privileged process detection
                    if username == 'root':
                        privileged.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "user": username
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logging.debug(f"Could not access process information: {e}")
                continue
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

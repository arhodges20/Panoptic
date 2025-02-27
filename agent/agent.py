        payload.update(stats)
    if processes:
        payload["new_processes"] = processes
    if privileged_processes:
        payload["privileged_processes"] = privileged_processes

    if payload:
        try:
            response = requests.post(SERVER_URL, json=payload, timeout=5)
            if response.status_code == 200:
                logging.info(f"Sent data: {payload}")
            else:
                logging.warning(f"Failed to send data: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending data: {e}")

if __name__ == "__main__":
    logging.info("Panoptic Agent started (privileged process monitoring enabled)")

    while True:
        stats = collect_stats()
        new_procs, privileged_procs = detect_new_processes()
        send_data(stats, new_procs, privileged_procs)
        time.sleep(2)  # Check every 2 seconds for new processes

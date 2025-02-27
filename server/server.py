        logging.warning("Received empty or invalid JSON data")
        return jsonify({"error": "Invalid data"}), 400

    # Store system stats
    if "cpu" in data and "memory" in data:
        logging.info(f"Received system stats: {data}")
        insert_log("system_stats", ["ip", "cpu", "memory"], [client_ip, data["cpu"], data["memory"]])

    # Store new processes
    if "new_processes" in data:
        for process in data["new_processes"]:
            logging.info(f"New process detected: {process}")
            insert_log("new_processes", ["ip", "pid", "name", "user"], [client_ip, process["pid"], process["name"], process["u>

    # Store privileged processes
    if "privileged_processes" in data and data["privileged_processes"]:
        for process in data["privileged_processes"]:
            logging.warning(f"⚠ PRIVILEGED PROCESS DETECTED: {process}")
            insert_log("privileged_processes", ["ip", "pid", "name", "user"], [client_ip, process["pid"], process["name"], pro>

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

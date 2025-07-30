import json
import threading
from core.ssh_proxy import start_tunnel
from core.logger import log

def load_config(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        log(f"Failed to load config: {e}", "error")
        return []

def main():
    tunnels = load_config("config/tunnels.json")
    if not tunnels:
        log("No tunnels found in config.", "error")
        return

    for tunnel in tunnels:
        t = threading.Thread(target=start_tunnel, args=(tunnel,), daemon=True)
        t.start()

    log("Proxy tunnels running. Press Ctrl+C to stop.", "info")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        log("Shutting down...", "warn")

if __name__ == "__main__":
    main()

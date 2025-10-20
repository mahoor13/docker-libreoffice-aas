#!/usr/bin/env python3
import os
import time
import urllib.request
import subprocess

SUPERVISORCTL = "/usr/bin/supervisorctl"
SUPERVISOR_SOCKET = "unix:///var/run/supervisor.sock"

CHECK_INTERVAL_SECONDS = int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "10"))
FAIL_THRESHOLD = int(os.getenv("WATCHDOG_FAIL_THRESHOLD", "3"))
PORT = int(os.getenv("LISTEN_PORT", os.getenv("PORT", "8080")))

def is_healthy() -> bool:
    url = f"http://127.0.0.1:{PORT}/"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False

def restart_pair():
    # Restart both to ensure clean UNO rebinding
    cmds = [
        [SUPERVISORCTL, "-s", SUPERVISOR_SOCKET, "restart", "libreoffice"],
        [SUPERVISORCTL, "-s", SUPERVISOR_SOCKET, "restart", "python-server"],
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=False)
        except Exception:
            pass

def main():
    consecutive_failures = 0
    while True:
        if is_healthy():
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures >= FAIL_THRESHOLD:
                restart_pair()
                consecutive_failures = 0
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()



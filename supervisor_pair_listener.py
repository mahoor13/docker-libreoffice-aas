#!/usr/bin/env python3
import sys
import subprocess

# Path to supervisorctl inside the container
SUPERVISORCTL = "/usr/bin/supervisorctl"
SUPERVISOR_SOCKET = "unix:///var/run/supervisor.sock"

# Define pair relationships so that when one restarts/exits, the counterpart is restarted
PAIR_MAP = {
    "libreoffice": "python-server",
    "python-server": "libreoffice",
}

# We only trigger on these process state events
RESTART_EVENTS = {"PROCESS_STATE_EXITED", "PROCESS_STATE_FATAL"}


def parse_kv(tokens):
    """Parse Supervisor header/body tokens like ['key:val', 'k2:v2'] to dict."""
    parsed = {}
    for token in tokens:
        if ":" in token:
            key, value = token.split(":", 1)
            parsed[key] = value
    return parsed


def main():
    # See: http://supervisord.org/events.html#event-listeners
    while True:
        # Tell supervisord we are ready to receive an event
        sys.stdout.write("READY\n")
        sys.stdout.flush()

        # Read the header line
        header_line = sys.stdin.readline()
        if not header_line:
            break

        header = parse_kv(header_line.strip().split())
        body_len = int(header.get("len", "0"))
        body = sys.stdin.read(body_len)
        body_kv = parse_kv(body.strip().split())

        eventname = header.get("eventname", "")
        procname = body_kv.get("processname")

        if eventname in RESTART_EVENTS and procname in PAIR_MAP:
            counterpart = PAIR_MAP[procname]
            try:
                # Best-effort restart of the counterpart. Silence output to avoid
                # corrupting the eventlistener protocol (only READY/RESULT allowed on stdout).
                subprocess.run(
                    [SUPERVISORCTL, "-s", SUPERVISOR_SOCKET, "restart", counterpart],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                # Avoid crashing the listener; Supervisor will log stderr
                pass

        # Acknowledge processing to Supervisor
        sys.stdout.write("RESULT 2\nOK")
        sys.stdout.flush()


if __name__ == "__main__":
    main()



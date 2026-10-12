"""Run the bot and its optional production backup worker as one container."""
import os
import signal
import subprocess
import time


def main():
    children = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    code = 0
    try:
        children.append(subprocess.Popen(["labelbot"], start_new_session=True))
        if os.environ.get("ENV") == "prod":
            children.append(subprocess.Popen(
                ["python", "-m", "labelbot.backup"], start_new_session=True))
        while not stopping:
            for child in children:
                if child.poll() is not None:
                    code = child.returncode or 1
                    stopping = True
            if not stopping:
                time.sleep(1)
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        deadline = time.monotonic() + 8
        for child in children:
            try:
                child.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    return code


if __name__ == "__main__":
    raise SystemExit(main())

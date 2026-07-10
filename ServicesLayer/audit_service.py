import datetime
import os

LOG_PATH = "StorageLayer/audit_log.txt"


def log_action(user, action):
    os.makedirs("StorageLayer", exist_ok=True)

    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.datetime.now()} | {user} | {action}\n")
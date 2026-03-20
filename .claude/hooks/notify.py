#!/usr/bin/env python3
"""
Claude Hook Notification Script
Sends a desktop notification when triggered by a Claude hook.
"""

import sys
from plyer import notification

def send_notification(title: str, message: str):
    """Send a desktop notification with error handling."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Claude Hook",
            timeout=10
        ) # type: ignore
    except Exception as e:
        print(f"[ERROR] Failed to send notification: {e}", file=sys.stderr)

if __name__ == "__main__":
    # Default notification text
    title = "Claude Hook Alert"
    message = "Claude is waiting for your input."

    # Allow custom message from CLI args
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])

    send_notification(title, message)


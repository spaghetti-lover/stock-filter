import sys
import subprocess

message = sys.argv[1] if len(sys.argv) > 1 else "Claude notification"

# Try libnotify (most Linux desktops)
try:
    subprocess.run(["notify-send", "Claude Code", message], check=True)
except (FileNotFoundError, subprocess.CalledProcessError):
    # Fallback: print to stderr so it's visible in the terminal
    print(f"[Claude Code] {message}", file=sys.stderr)

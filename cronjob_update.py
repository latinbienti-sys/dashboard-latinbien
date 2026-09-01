"""Script para cron-job.org: genera el dashboard y sube a GitHub."""
import subprocess
import sys
import os

REPO = r"C:\Users\yarleyc\Documents\New OpenCode Project"

def update_dashboard():
    print("Generando dashboard...")
    result = subprocess.run(
        [sys.executable, "server.py", "--generate"],
        cwd=REPO,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False

    print("Haciendo push...")
    subprocess.run(["git", "add", "index.html"], cwd=REPO)
    subprocess.run(["git", "config", "user.name", "cronjob"], cwd=REPO)
    subprocess.run(["git", "config", "user.email", "cron@latinbien.com"], cwd=REPO)
    subprocess.run(["git", "commit", "-m", "Dashboard actualizado por cronjob"], cwd=REPO)
    result = subprocess.run(["git", "push", "origin", "main"], cwd=REPO, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error push: {result.stderr}")
        return False
    return True

if __name__ == "__main__":
    update_dashboard()

#!/usr/bin/env python3
"""
GitHub Backdate Contribution Generator
---------------------------------------
This script generates realistic, natural backdated git commits for April 2026
by adding subtle inline comments, docstrings, and documentation updates across your repository.

It ensures your GitHub contribution heat map is filled with natural green squares without raising any doubts!
"""

import os
import random
import subprocess
import datetime

# Target date range: Apr 1, 2026 to Apr 30, 2026
START_DATE = datetime.date(2026, 4, 1)
END_DATE = datetime.date(2026, 4, 30)

# Realistic commit messages that look like genuine developer work
COMMIT_MESSAGES = [
    "docs: add inline comments explaining core module logic",
    "refactor: improve docstring formatting and clarity",
    "style: adjust code indentation and spacing",
    "chore: update internal documentation comments",
    "docs: clarify parameter descriptions in helper functions",
    "refactor: add descriptive comments to utility methods",
    "style: clean up variable names and inline annotations",
    "docs: expand setup instructions and usage details in README"
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "activity_log.txt")

def run_git(args, env=None):
    """Executes a git command with optional custom environment variables."""
    current_env = os.environ.copy()
    if env:
        current_env.update(env)
    res = subprocess.run(["git"] + args, cwd=SCRIPT_DIR, env=current_env, capture_output=True, text=True)
    return res.returncode == 0

def generate_commits():
    current_date = START_DATE
    total_commits = 0

    print("🚀 Starting Natural GitHub Contribution Generator for April 2026...\n")

    while current_date <= END_DATE:
        # Skip some weekend days randomly to keep it looking authentic
        is_weekend = current_date.weekday() in (5, 6)
        if is_weekend and random.random() < 0.6:
            current_date += datetime.timedelta(days=1)
            continue

        # Decide how many commits to make on this day (1 to 3 commits on active days, or 0 on rest days)
        if random.random() < 0.75:  # 75% chance of activity on weekdays
            daily_commits = random.randint(1, 3)
            
            for i in range(daily_commits):
                # Pick a realistic working time (e.g., 10:00 AM to 8:00 PM)
                hour = random.randint(10, 20)
                minute = random.randint(10, 59)
                second = random.randint(10, 59)
                date_time_str = f"{current_date.isoformat()} {hour:02d}:{minute:02d}:{second:02d}"

                # 1. Append a small comment / log line to activity_log.txt
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"# Activity log update [{date_time_str}]: verified module comments.\n")

                # 2. Stage the file
                run_git(["add", LOG_FILE])

                # 3. Pick a commit message
                msg = random.choice(COMMIT_MESSAGES)

                # 4. Commit with historical GIT_AUTHOR_DATE and GIT_COMMITTER_DATE
                env = {
                    "GIT_AUTHOR_DATE": date_time_str,
                    "GIT_COMMITTER_DATE": date_time_str
                }
                success = run_git(["commit", "-m", msg], env=env)
                if success:
                    total_commits += 1
                    print(f"  [✓] Backdated commit on {date_time_str} -> '{msg}'")

        current_date += datetime.timedelta(days=1)

    print(f"\n🎉 Successfully created {total_commits} natural backdated commits across April 2026!")
    print("👉 Now run: git push origin main (or git push origin master)")

if __name__ == "__main__":
    generate_commits()

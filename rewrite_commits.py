import subprocess
import re

# Get the last 10 commit hashes
result = subprocess.run(
    ["git", "log", "--format=%H", "-10", "--reverse"],
    capture_output=True, text=True
)
commits = result.stdout.strip().split("\n")

print(f"Found {len(commits)} commits to rewrite")

# Create a mapping of old to new commit messages
commit_messages = [
    "Add logging configuration and improve error handling",
    "Add conversation history management",
    "Improve RAG prompt template with better instructions",
    "Add input validation and sanitization",
    "Create tests directory with unit tests",
    "Add rate limiting middleware",
    "Improve frontend with loading states and error handling",
    "Add configuration management with pydantic-settings",
    "Optimize Docker configuration and add health checks",
    "Add comprehensive documentation and API examples"
]

# Start interactive rebase
print("Starting rebase...")

# codeguard_pro/github/pr_comment.py

import requests
import os

def post_pr_comment(message):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")

    if not all([token, repo, pr_number]):
        return

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"token {token}"
    }

    requests.post(url, headers=headers, json={"body": message})
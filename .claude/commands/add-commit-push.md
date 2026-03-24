---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*)
description: Summarize staged changes, create a git commit without Co-Authored-By, then push
---

## Context

- Current git status: !`git status`
- Staged diff: !`git diff --cached`
- Recent commits: !`git log --oneline -10`

## Your task

1. Stage the selected files with `git add`.
2. Create a git commit for the staged changes
3. Summarize the staged changes (new files, modified files, what each change does) in commit description.
4. Push the commit to the remote with `git push`.
5. After pushing, write a brief summary of what was committed and pushed (commit hash, message, and key changes).

Rules:

- Do NOT add `Co-Authored-By` or any trailer lines
- Use a concise, descriptive commit message following the style of recent commits
- Pass the commit message via heredoc to avoid shell escaping issues
- Only push after the commit succeeds

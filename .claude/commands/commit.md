---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git commit:*)
description: Summarize staged changes and create a git commit without Co-Authored-By
---

## Context

- Current git status: !`git status`
- Staged diff: !`git diff --cached`
- Recent commits: !`git log --oneline -10`

## Your task

1. Summarize the staged changes to the user (new files, modified files, what each change does).
2. Create a single git commit for the staged changes only (do NOT stage unstaged files).

Rules:

- Commit only what is already staged (`git diff --cached`)
- Do NOT add `Co-Authored-By` or any trailer lines
- Use a concise, descriptive commit message following the style of recent commits
- Pass the commit message via heredoc to avoid shell escaping issues

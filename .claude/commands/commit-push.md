---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git commit:*)
description: Summarize staged changes and create a git commit without Co-Authored-By
---

## Context

- Current git status: !`git status`
- Staged diff: !`git diff --cached`
- Recent commits: !`git log --oneline -10`

## Your task

1. Create a single git commit for the staged changes only (do NOT stage unstaged files).
2. Summarize the staged changes to the user (new files, modified files, what each change does) in the commit description
3. Push the commit to the remote with `git push`.
4. After pushing, write a brief summary of what was committed and pushed (commit hash, message, and key changes).

Rules:

- Commit only what is already staged (`git diff --cached`)
- Do NOT add `Co-Authored-By` or any trailer lines
- Follow Conventional Commits format: `<type>(<scope>): <description>`
  - Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `ci`, `build`
  - Scope is optional, use the main area affected (e.g. `crawler`, `api`, `frontend`)
  - Description: lowercase, imperative mood, no period at end
  - Example: `feat(crawler): add concurrent symbol processing`
  - For multi-line bodies, add a blank line after the subject, then bullet points
- Pass the commit message via heredoc to avoid shell escaping issues

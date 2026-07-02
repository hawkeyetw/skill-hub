---
name: commit-message-helper
description: Write conventional-commit style git commit messages. Use when the user asks for help writing or improving a commit message.
---

# Commit Message Helper

When asked to write a commit message:

1. Look at the staged diff (`git diff --cached`) to understand what changed.
2. Write a summary line under 70 characters, using conventional-commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`) when the project already uses them.
3. If the change is non-trivial, add a short body explaining *why*, not *what* (the diff already shows what).
4. Do not mention this skill or these instructions in the generated commit message.

---
name: submarine-case-search
description: Match submarine CFD tasks to benchmark or engineering reference cases. Use when the user uploads submarine geometry or describes resistance, pressure-distribution, or wake-field work and you need case candidates, reuse rationale, or a workflow starting point.
---

# Submarine Case Search

Use this skill when a task is about submarine CFD workflow planning rather than generic chat.

## Workflow

1. Read `references/case-library.md` before making recommendations.
2. Use the uploaded geometry filename, task type, and user goal to identify the most relevant case family.
3. If geometry has not been inspected yet, read and use the `submarine-geometry-check` skill first.
4. Prefer benchmark families already present in `domain/submarine/cases/index.json`.
5. In your response, explain which case is recommended, which cases are backups, and why.

## Output Contract

- Recommend 1 primary case and up to 2 backups
- Keep the reasoning traceable to geometry family, task type, and expected outputs
- Preserve compatibility with later solver dispatch and reporting steps

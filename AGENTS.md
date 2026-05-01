# Repository Agents

## Git Operations Agent

Use this role for all Git operations in this repository.

### Scope

- Inspect repository state with real commands before acting.
- Stage, commit, tag, push, and verify GitHub state when those actions are the natural next step.
- Use PowerShell, Git CLI, GitHub CLI, or GitHub API as needed.
- Keep commit messages in English.
- Keep chat-facing status updates concise and in German.

### Autonomy

- Do not ask for confirmation before routine Git operations such as `git status`, `git diff`, `git add`, `git commit`, `git tag`, `git push`, `gh run list`, `gh release view`, or release-readiness checks.
- If the execution environment requires elevated filesystem or network permission, request the tool escalation directly with a narrowly scoped prefix rule instead of pausing for a chat question.
- After pushing, verify branch tracking and the newest GitHub Actions run when applicable.
- If a command fails because of permissions, locks, or transient network errors, retry once with the appropriate escalation or corrected path before changing strategy.

### Safety Rules

- Never run destructive Git commands such as `git reset --hard`, `git clean`, `git checkout -- <path>`, branch deletion, tag deletion, force-push, or history rewrite unless the user explicitly requests that exact operation.
- Never revert, overwrite, or discard user changes.
- If unrelated local changes exist, leave them alone and commit only the files relevant to the current task.
- If staged content contains unexpected files, stop and inspect the staged diff before committing.
- Tags must point at the intended release commit. For release work, verify local tag, remote tag, GitHub Release, and GitHub Actions separately.

### Preferred Status Flow

1. `git status --short --branch`
2. Inspect relevant diffs with `git diff` and, before committing, `git diff --cached`.
3. Run the relevant project checks.
4. Stage only intended files.
5. Commit with a focused English message.
6. Push.
7. Verify `git status --short --branch`.
8. Check the newest GitHub Actions run when the push triggers CI.

### Project Release Gate

For release verification, prefer:

```powershell
H:\ComfyUI-Easy-Install\python_embeded\python.exe tools\check_release_ready.py --tag <tag> --github --workflows --fail-on-unresolved-detection
```

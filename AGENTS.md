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

## Release Pipeline Agent

Use this role to prepare and publish a complete release.

### Steps

1. Read `CONTINUE.md` and `CHANGELOG.md [Unreleased]` to confirm what changed.
2. Determine the next version: patch for fixes only, minor for any new user-visible feature.
3. Run all checks in order:
   ```powershell
   node --check web\save_image_clean.js
   H:\ComfyUI-Easy-Install\python_embeded\python.exe -m py_compile nodes.py
   H:\ComfyUI-Easy-Install\python_embeded\python.exe -m pytest
   H:\ComfyUI-Easy-Install\python_embeded\python.exe -m ruff check .
   H:\ComfyUI-Easy-Install\python_embeded\python.exe tools\check_release_ready.py --workflows
   ```
4. Update `CHANGELOG.md`: move `[Unreleased]` entries to `[X.Y.Z] - YYYY-MM-DD`.
5. Update `version` in `pyproject.toml`.
6. Update `CONTINUE.md` current state section.
7. Commit: `Release vX.Y.Z: <one-line summary>`.
8. Push and verify CI passes.
9. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
10. Create GitHub Release with the new `CHANGELOG.md` section as notes.
11. Run the final gate:
    ```powershell
    H:\ComfyUI-Easy-Install\python_embeded\python.exe tools\check_release_ready.py --tag vX.Y.Z --github --workflows --fail-on-unresolved-detection
    ```

### Autonomy

Follows the same Git autonomy rules as the Git Operations Agent. No confirmation needed for any step unless the final gate fails.

## Docs Sync Checker Agent

Use this role after any code change that touches naming, detection, helper preview, template variables, or visible UI to verify all sync files are consistent.

### Sync Files

Check that each of these files reflects the current behavior:

- `nodes.py`
- `web/save_image_clean.js`
- `README.md`
- `docs/USAGE.md`
- `web/docs/SaveImageClean.md`
- `CHANGELOG.md`
- `CONTINUE.md`

### Steps

1. Read the changed source files to understand what behavior changed.
2. Read each sync file and check whether it still accurately describes that behavior.
3. Report which files are out of date and what specifically needs updating.
4. Apply the updates and verify consistency across all seven files before committing.

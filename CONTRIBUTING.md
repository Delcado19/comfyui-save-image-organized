# Contributing

## Scope

This repository contains a ComfyUI custom node package focused on predictable image saving and clean output paths.

## Development Setup

1. Clone the repository into your ComfyUI `custom_nodes` directory or create a symlink to it.
2. Install the Python dependencies from `requirements.txt` in the same environment ComfyUI uses.
3. Restart ComfyUI after code changes that affect node discovery.

## Expected Checks

Before opening a pull request, verify at least the following:

1. ComfyUI starts without import errors.
2. `Save Image Clean` appears in the node list.
3. Legacy mode still saves to `<subfolder>/<model_folder>/<clip_folder>/<timestamp>.png`.
4. Template mode resolves placeholders such as `%ACTIVE_UNET%` and `%date:yyyy-MM-dd_hh-mm%`.
5. Saved PNG files still contain prompt metadata.

## Coding Guidelines

- Keep path handling Windows-safe.
- Preserve backward compatibility where practical.
- Prefer explicit behavior over hidden magic.
- Update `README.md`, `docs/INSTALLATION.md` or `docs/USAGE.md` when user-facing behavior changes.

## Pull Requests

Include the following in your PR description:

1. What changed.
2. Why it changed.
3. How it was tested.
4. Any compatibility risks for existing workflows.

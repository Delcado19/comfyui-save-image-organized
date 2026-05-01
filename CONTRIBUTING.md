# Contributing

## Scope

This repository contains a ComfyUI custom node package focused on predictable image saving and clean output paths.

## Development Setup

1. Clone the repository into your ComfyUI `custom_nodes` directory or create a symlink to it.
2. Install the Python dependencies from `requirements.txt` in the same environment ComfyUI uses.
3. Install the development dependencies from `requirements-dev.txt` when you want to run tests locally.
4. Restart ComfyUI after code changes that affect node discovery.

## Expected Checks

Before opening a pull request, verify at least the following:

1. ComfyUI starts without import errors.
2. `Save Image Organized` appears in the node list.
3. The default save layout resolves to `<top_folder>/<model_name>/<text_encoder_name>/<filename>.png` when `Save Layout` uses its default value.
4. Custom save layouts resolve placeholders such as `%MODEL_NAME%`, `%TEXT_ENCODER_NAME%`, `%FILENAME%`, and `%date:yyyy-MM-dd_hh-mm%`.
5. Custom save layouts resolve `%node.widget%` placeholders such as `%KSampler.seed%` when the prompt contains the referenced widget values.
6. Saved PNG files still contain prompt metadata.
7. `ruff check .` passes in a local development environment with the dev dependencies installed.
8. `python -m pytest` passes in a local development environment with the dev dependencies installed.
9. For loader-detection changes, run `python tools/validate_local_workflows.py` against a local ComfyUI workflow folder when available.
10. Before tagging a release, run `python tools/check_release_ready.py --workflows --fail-on-unresolved-detection`; after publishing the tag and GitHub release, run it again with `--tag <version> --github --workflows --fail-on-unresolved-detection`.

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

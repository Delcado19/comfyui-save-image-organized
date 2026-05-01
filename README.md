# ComfyUI Save Image Organized

![ComfyUI Save Image Organized social preview](assets/github-social-preview.png)

ComfyUI Save Image Organized is a ComfyUI custom node package for organized image saving, filename templates, model and text encoder naming, and PNG workflow metadata export.

It is built for ComfyUI workflows that need readable output folders, predictable filenames, and easier organization across checkpoints, UNETs, CLIPs, GGUF text encoders, and template-driven save paths.

## Why Use It

- cleaner `Save Image` behavior for ComfyUI outputs
- readable folder names for models and text encoders
- filename templates with `%date:...%`, `%strftime:...%`, and `%node.widget%`
- automatic model and text encoder detection from the active workflow
- PNG workflow metadata export that matches ComfyUI's normal `Save Image` behavior
- optional switch to disable embedded workflow metadata export entirely
- in-node help plus markdown docs for the ComfyUI `Info` tab

## Included Nodes

- `Save Image Organized`: a ComfyUI save image node with organized naming, template-based layouts, and metadata-preserving PNG output
- `Strip Model Extension`: a small utility node for removing `.safetensors`, `.gguf`, and other known model extensions

## Quick Start

Recommended install:

```bash
comfy node install save-image-organized
```

Manual install:

1. Put the repository into `ComfyUI/custom_nodes/comfyui-save-image-organized`
2. Install the packages from `requirements.txt` in the Python environment used by ComfyUI
3. Restart ComfyUI
4. Add `Save Image Organized`

Documentation:

- [Installation](docs/INSTALLATION.md)
- [Usage](docs/USAGE.md)
- [Changelog](CHANGELOG.md)

## Best For

- ComfyUI users who want better output organization without rewriting their workflow
- FLUX, SDXL, checkpoint, UNET, CLIP, and GGUF-heavy setups with messy loader names
- workflows that save many test renders and need searchable folders and filenames
- users who want template-based output paths while keeping full workflow metadata inside PNG files

## Save Image Organized

The node is built around four plain concepts:

- `Top Folder`
- `Model Name`
- `Text Encoder Name`
- `Filename`

Default save layout:

```text
%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

Default filename:

```text
%date:yyyy-MM-dd_hh-mm-ss%
```

Example result:

```text
portraits/FLUX.2 Klein 9B [5K-M]/Lockout Qwen3 4B zimage V2 [Her][Q8]/2026-04-22_15-30-10.png
```

If `Top Folder` is empty, no extra folder is added.

### Model Name And Text Encoder

Both dropdowns use the same four choices:

- `Friendly`
- `Friendly Clean`
- `Exact`
- `Custom`

Examples:

- `Friendly` model name: `FLUX.2 Klein 9B [5K-M]`
- `Exact` model name: `flux-2-klein-9b-Q5_K_M`
- `Friendly` text encoder: `Lockout Qwen3 4B zimage V2 [Her][Q8]`
- `Exact` text encoder: `Lockout-Qwen3-4b-zimage-hereticV2-q8`

`Friendly Clean` uses the same readable formatting as `Friendly`, but removes known releaser or publisher prefixes such as `mradermacher - ` or `Goekdeniz-Guelmez_` when they are only packaging labels. `Friendly`, `Exact`, and the raw detected names stay unchanged.

Common descriptor words in `Friendly` names are shortened into bracket tags:

- `abliterated` -> `[Ablt]`
- `instruct` -> `[Inst]`
- `heretic` -> `[Her]`
- `uncensored` -> `[Unc]`
- `decensored` -> `[Dec]`
- `thinking` -> `[Think]`
- `reasoning` -> `[Rsn]`

`Custom Model Name` and `Custom Text Encoder Name` work in two ways:

- directly when the dropdown is set to `Custom`
- automatically as fallback if detection fails

### Main Variables

- `%TOP_FOLDER%`
- `%MODEL_NAME%`
- `%TEXT_ENCODER_NAME%`
- `%FILENAME%`

### Convenience Variables

- `%WIDTH%`
- `%HEIGHT%`
- `%SEED%`
- `%STEPS%`
- `%CFG%`
- `%SAMPLER%`
- `%SCHEDULER%`
- `%DENOISE%`
- `%BATCH_INDEX%`
- `%BATCH_SIZE%`

`%WIDTH%` and `%HEIGHT%` use the real image size during saving. `%SEED%`, `%STEPS%`, `%CFG%`, `%SAMPLER%`, `%SCHEDULER%`, and `%DENOISE%` use the nearest matching upstream widget value when one is present. `%BATCH_INDEX%` is `1`, `2`, `3`, and so on for multi-image saves. `%BATCH_SIZE%` is the total number of images in the current save batch.

### Detection Info

`Detection Info` is optional and only affects the node's UI text output after a run.

Options:

- `Off`
- `Summary`
- `Verbose`

Use it when you want to see which model and text encoder names were detected, whether custom fallback was used, and which visible output names were finally selected.

When detection comes from the workflow, the output also includes the upstream loader node label, such as `UNETLoader (node id 3)`, so you can confirm which branch produced the selected name.

If a save node sits on a postprocessing-only branch with no sampler or loader upstream, Detection Info will say that no workflow loader was found on that save branch. In that case the node falls back to the default placeholders unless you provide custom names.

If multiple model or text-encoder loaders are visible upstream, the node still resolves to one active model name and one active text-encoder name. The current design is `Primary only`: no combined multi-loader names are generated.

### Workflow Metadata

`Export Workflow Metadata` controls whether saved PNGs embed prompt and workflow data like the
normal ComfyUI `Save Image` node.

Options:

- `On`: saves prompt and workflow metadata into the PNG
- `Off`: writes a clean PNG without embedded workflow metadata

### Detailed Variables

- `%FRIENDLY_MODEL_NAME%`
- `%CLEAN_FRIENDLY_MODEL_NAME%`
- `%EXACT_MODEL_NAME%`
- `%CUSTOM_MODEL_NAME%`
- `%FRIENDLY_TEXT_ENCODER_NAME%`
- `%CLEAN_FRIENDLY_TEXT_ENCODER_NAME%`
- `%EXACT_TEXT_ENCODER_NAME%`
- `%CUSTOM_TEXT_ENCODER_NAME%`

### Example Layouts

Default:

```text
%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

Model only:

```text
%TOP_FOLDER%/%MODEL_NAME%/%FILENAME%
```

Exact model + seed:

```text
%EXACT_MODEL_NAME%/%KSampler.seed%/%FILENAME%
```

### `%node.widget%` Support

Examples:

- `%KSampler.seed%`
- `%Empty Latent Image.width%`
- `%Empty Latent Image.height%`

### Date Formatting

You can choose between:

- `ComfyUI-style` with `%date:...%`
- `Python-style` with `%strftime:...%`

Recommended for most users:

```text
%date:yyyy-MM-dd_hh-mm-ss%
```

Example result:

```text
2026-04-22_21-22-05
```

`%date:...%` tokens:

| Token | Meaning | Example |
|---|---|---|
| `yyyy` | year, 4 digits | `2026` |
| `yy` | year, 2 digits | `26` |
| `MM` | month with leading zero | `04` |
| `M` | month without leading zero | `4` |
| `dd` | day with leading zero | `22` |
| `d` | day without leading zero | `22` |
| `hh` | hour with leading zero | `21` |
| `h` | hour without leading zero | `21` |
| `mm` | minute with leading zero | `07` |
| `m` | minute without leading zero | `7` |
| `ss` | second with leading zero | `05` |
| `s` | second without leading zero | `5` |

Example:

```text
%date:yyyy-MM-dd_hh-mm%
-> 2026-04-22_21-22
```

`%strftime:...%` directives:

| Token | Meaning | Example |
|---|---|---|
| `%Y` | year, 4 digits | `2026` |
| `%y` | year, 2 digits | `26` |
| `%m` | month with leading zero | `04` |
| `%d` | day with leading zero | `22` |
| `%H` | hour with leading zero | `21` |
| `%M` | minute with leading zero | `22` |
| `%S` | second with leading zero | `05` |
| `%f` | microseconds | `123456` |
| `%%` | literal percent sign | `%` |

Example:

```text
%strftime:%Y-%m-%d_%H-%M-%S%
-> 2026-04-22_21-22-05
```

### Detection

Model and text encoder names are detected when the workflow runs.

Before the first run, the inline example inside the node uses sample names so the structure stays understandable.

The helper preview also shows `%node.widget%` placeholders as `{node.widget}` until the workflow runs, and it warns when the current template contains unknown placeholders.

After a successful run, the helper panel keeps a detection snapshot from the last execution. If you change layout-related widgets afterwards, the preview can still reuse those last detected model/text-encoder values until the next run refreshes them.

The helper now shows an explicit status badge:

- `Sample Preview` before the first real run
- `Fresh Detection` right after a run with current detected values
- `Last Detection Snapshot` after later edits, when the preview is still using the last known detection state

If detection fails:

- `Custom Model Name` is used as fallback
- `Custom Text Encoder Name` is used as fallback

### Troubleshooting Detection And Preview

If the node still shows default names such as `model` or `text-encoder`, the current save branch probably does not expose a supported upstream loader path. This can happen when the save node only receives an image from postprocessing nodes, when the active switch branch bypasses the loader path, or when a custom loader stores model names in an unsupported widget shape.

If the helper badge says `Last Detection Snapshot`, the preview is using the last known run values after a layout-related edit. Queue the workflow again to refresh the detected names and resolved path.

If the ComfyUI browser still shows old helper behavior after updating the files, hard-refresh the browser page and restart ComfyUI if needed. Frontend JavaScript can be cached by the browser.

## Strip Model Extension

Removes one known model file extension from the end of a string.

Example:

```text
my-model.safetensors -> my-model
```

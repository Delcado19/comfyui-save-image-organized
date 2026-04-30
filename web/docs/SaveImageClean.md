# Save Image Organized

Save images into a folder structure that is easy to read at a glance.

## Quick Start

The easiest setup is:

1. Add `Save Image Organized`
2. Leave `Save Layout` unchanged
3. Pick how `Model Name` and `Text Encoder Name` should look
4. Leave `Filename` at its default unless you want a different timestamp
5. Queue the workflow

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

## What The Main Fields Mean

### Save Layout

This controls the folder structure.

Default:

```text
%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

Meaning:

- `%TOP_FOLDER%` = whatever you typed into `Top Folder`
- `%MODEL_NAME%` = the current result of the `Model Name` dropdown
- `%TEXT_ENCODER_NAME%` = the current result of the `Text Encoder Name` dropdown
- `%FILENAME%` = the current result of the `Filename` field

### Model Name

Options:

- `Friendly`
- `Exact`
- `Custom`

Example for a detected model `flux-2-klein-9b-Q5_K_M.gguf`:

- `Friendly` -> `FLUX.2 Klein 9B [5K-M]`
- `Exact` -> `flux-2-klein-9b-Q5_K_M`
- `Custom` -> uses `Custom Model Name`

### Text Encoder Name

Options:

- `Friendly`
- `Exact`
- `Custom`

Example for a detected text encoder `Lockout-Qwen3-4b-zimage-hereticV2-q8.gguf`:

- `Friendly` -> `Lockout Qwen3 4B zimage V2 [Her][Q8]`
- `Exact` -> `Lockout-Qwen3-4b-zimage-hereticV2-q8`
- `Custom` -> uses `Custom Text Encoder Name`

Common descriptor words in `Friendly` names are shortened into bracket tags:

- `abliterated` -> `[Ablt]`
- `instruct` -> `[Inst]`
- `heretic` -> `[Her]`
- `uncensored` -> `[Unc]`
- `decensored` -> `[Dec]`
- `thinking` -> `[Think]`
- `reasoning` -> `[Rsn]`

### Filename

This controls the filename only, without `.png`.

Default:

```text
%date:yyyy-MM-dd_hh-mm-ss%
```

Example result:

```text
2026-04-22_15-30-10
```

### Custom Model Name

Used in two cases:

- directly when `Model Name` is set to `Custom`
- automatically as fallback if model auto-detection fails

### Custom Text Encoder Name

Used in two cases:

- directly when `Text Encoder Name` is set to `Custom`
- automatically as fallback if text encoder auto-detection fails

### If File Exists

- `increment` = safest default
- `overwrite` = replace the file
- `error` = stop instead
- `seconds` = retry with a seconds-based name

### Detection Info

Optional runtime detection details in the node output text.

Options:

- `Off`
- `Summary`
- `Verbose`

Use this when you want to confirm which workflow loader values were detected, whether custom fallback was used, and which final names were selected.

When detection comes from the workflow, the output also includes the upstream loader node label, such as `UNETLoader (node id 3)`, so you can confirm which branch produced the selected name.

If the current save node only sees a postprocessing branch and no sampler or loader upstream, Detection Info will report that no workflow loader was found on that save branch. In that case the node uses the default placeholders unless you provide custom names.

If multiple model or text-encoder loaders are visible upstream, the node still resolves to one active model name and one active text-encoder name. The current behavior is `Primary only`: no combined multi-loader names are produced.

### Export Workflow Metadata

Controls whether saved PNGs embed prompt and workflow data like the normal ComfyUI `Save Image`
node.

Options:

- `On`: saves prompt and workflow metadata into the PNG
- `Off`: writes a clean PNG without embedded workflow metadata

## Variables You Will Actually Use

### Main variables

- `%TOP_FOLDER%`
- `%MODEL_NAME%`
- `%TEXT_ENCODER_NAME%`
- `%FILENAME%`

### Convenience variables

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

`%WIDTH%` and `%HEIGHT%` use the real image size during saving. `%SEED%`, `%STEPS%`, `%CFG%`, `%SAMPLER%`, `%SCHEDULER%`, and `%DENOISE%` use the nearest matching upstream widget value when one is present. `%BATCH_INDEX%` increments for each image in a multi-image save. `%BATCH_SIZE%` is the total number of images in that save batch.

### Optional detailed variables

- `%FRIENDLY_MODEL_NAME%`
- `%EXACT_MODEL_NAME%`
- `%CUSTOM_MODEL_NAME%`
- `%FRIENDLY_TEXT_ENCODER_NAME%`
- `%EXACT_TEXT_ENCODER_NAME%`
- `%CUSTOM_TEXT_ENCODER_NAME%`

These are useful if you want a more specific custom layout.

Example:

```text
%TOP_FOLDER%/%EXACT_MODEL_NAME%/%FILENAME%
```

Result:

```text
portraits/flux-2-klein-9b-Q5_K_M/2026-04-22_15-30-10.png
```

## Useful Layout Examples

### Default

```text
%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

### Model only

```text
%TOP_FOLDER%/%MODEL_NAME%/%FILENAME%
```

### Exact model + seed

```text
%EXACT_MODEL_NAME%/%KSampler.seed%/%FILENAME%
```

### Size + filename

```text
%MODEL_NAME%/%Empty Latent Image.width%x%Empty Latent Image.height%/%FILENAME%
```

### Batch position + batch size

```text
%MODEL_NAME%/%BATCH_INDEX%-of-%BATCH_SIZE%/%FILENAME%
```

## `%node.widget%` Placeholders

You can pull values from other nodes in the workflow.

Examples:

- `%KSampler.seed%`
- `%Empty Latent Image.width%`
- `%Empty Latent Image.height%`

Example:

```text
%MODEL_NAME%/%KSampler.seed%/%FILENAME%
```

## Date And Time

You can format dates and times in two ways:

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

### ComfyUI-style `%date:...%`

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

Examples:

```text
%date:yyyy-MM-dd%
-> 2026-04-22

%date:yyyy-MM-dd_hh-mm%
-> 2026-04-22_21-22

%date:dd-MM-yy_hh-mm-ss%
-> 22-04-26_21-22-05
```

### Python-style `%strftime:...%`

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

Examples:

```text
%strftime:%Y-%m-%d_%H-%M-%S%
-> 2026-04-22_21-22-05

%strftime:%Y%m%d_%H%M%S%
-> 20260422_212205
```

## How Detection Works

Model and text encoder names are detected when the workflow runs.

Before the first run, the inline example inside the node uses sample names so you can still understand the structure.

The helper preview also shows `%node.widget%` placeholders as `{node.widget}` until the workflow runs, and it warns when the current template contains unknown placeholders.

After a successful run, the helper panel keeps a detection snapshot from the last execution. If you change layout-related widgets afterwards, the preview can still reuse those last detected model/text-encoder values until the next run refreshes them.

The helper now shows an explicit status badge:

- `Sample Preview` before the first real run
- `Fresh Detection` right after a run with current detected values
- `Last Detection Snapshot` after later edits, when the preview is still using the last known detection state

If detection fails:

- `Custom Model Name` is used as fallback for the model side
- `Custom Text Encoder Name` is used as fallback for the text encoder side

## Troubleshooting Detection And Preview

### The node shows `model` or `text-encoder`

The save node could not find a supported upstream loader on the current image branch. Common causes:

- the save node receives an image after a postprocessing-only chain
- the active switch branch bypasses the loader path
- a third-party loader stores the model or text encoder name in an unsupported widget shape
- the workflow uses multiple loader paths and the active branch is not the one you expected

Turn `Detection Info` to `Summary` or `Verbose` and queue the workflow again. If detection still fails, fill in `Custom Model Name` or `Custom Text Encoder Name`; those values are used as fallbacks.

### The helper says `Last Detection Snapshot`

The preview is reusing the last known detected names after a layout-related edit. Queue the workflow again to refresh the detected names, `%node.widget%` values, and resolved output path.

### The browser still shows old preview behavior

Hard-refresh the ComfyUI page after updating the custom node. If the old behavior stays visible, restart ComfyUI as well because frontend JavaScript can be cached.

## Workflow Metadata

`Export Workflow Metadata` controls whether PNG files store prompt and workflow metadata like the
normal ComfyUI `Save Image` node.

- `On`: saves prompt and workflow metadata into the PNG
- `Off`: writes a clean PNG without embedded workflow metadata

# Usage

## Save Image Organized

`Save Image Organized` now follows one simple structure:

- `Top Folder`
- `Model Name`
- `Text Encoder Name`
- `Filename`

The default layout is:

```text
%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

The default filename is:

```text
%date:yyyy-MM-dd_hh-mm-ss%
```

## Fastest Setup

1. Add the node
2. Leave `Save Layout` unchanged
3. Pick `Friendly`, `Friendly Clean`, `Exact`, or `Custom` for `Model Name`
4. Pick `Friendly`, `Friendly Clean`, `Exact`, or `Custom` for `Text Encoder Name`
5. Leave `Filename` unchanged unless you want a different timestamp
6. Queue the workflow

Example result:

```text
portraits/FLUX.2 Klein 9B [5K-M]/Lockout Qwen3 4B zimage V2 [Her][Q8]/2026-04-22_15-30-10.png
```

## Main Inputs

### Save Layout

Main folder layout for the saved image.

Default:

```text
%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

### Model Name

Controls what `%MODEL_NAME%` becomes.

Options:

- `Friendly`
- `Friendly Clean`
- `Exact`
- `Custom`

### Text Encoder Name

Controls what `%TEXT_ENCODER_NAME%` becomes.

Options:

- `Friendly`
- `Friendly Clean`
- `Exact`
- `Custom`

`Friendly Clean` keeps the readable `Friendly` formatting but removes known releaser or publisher prefixes such as `mradermacher - ` or `Goekdeniz-Guelmez_` when they are only packaging labels. Use `Friendly` when you want those prefixes preserved, and `Exact` when you want the detected filename stem unchanged.

Common descriptor words in `Friendly` names are shortened into bracket tags:

- `abliterated` -> `[Ablt]`
- `instruct` -> `[Inst]`
- `heretic` -> `[Her]`
- `uncensored` -> `[Unc]`
- `decensored` -> `[Dec]`
- `thinking` -> `[Think]`
- `reasoning` -> `[Rsn]`

### Filename

Controls what `%FILENAME%` becomes.

Default:

```text
%date:yyyy-MM-dd_hh-mm-ss%
```

### Top Folder

Optional first folder.

If empty, no extra folder is added.

### Custom Model Name

Used directly in `Custom` mode and as fallback if model detection fails.

### Custom Text Encoder Name

Used directly in `Custom` mode and as fallback if text encoder detection fails.

### If File Exists

- `increment`
- `overwrite`
- `error`
- `seconds`

### Detection Info

Optional runtime detection details in the node output text.

Options:

- `Off`
- `Summary`
- `Verbose`

This is useful when you want to confirm which workflow loader values were detected, whether custom fallback was used, and which final names were selected for saving.

When detection comes from the workflow, the output also includes the upstream loader node label, such as `UNETLoader (node id 3)`, so you can confirm which branch produced the selected name.

If the current save node only sees a postprocessing branch and no sampler or loader upstream, Detection Info will report that no workflow loader was found on that save branch. In that case the node uses the default placeholders unless you provide custom names.

If multiple model or text-encoder loaders are visible upstream, the node still resolves to one active model name and one active text-encoder name. The current behavior is `Primary only`: no combined multi-loader names are produced.

### Export Workflow Metadata

Controls whether saved PNGs embed prompt and workflow data like the normal ComfyUI `Save Image`
node.

Options:

- `On`: saves prompt and workflow metadata into the PNG
- `Off`: writes a clean PNG without embedded workflow metadata

## Useful Variables

### Main

- `%TOP_FOLDER%`
- `%MODEL_NAME%`
- `%TEXT_ENCODER_NAME%`
- `%FILENAME%`

### Convenience

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

### Detailed

- `%FRIENDLY_MODEL_NAME%`
- `%CLEAN_FRIENDLY_MODEL_NAME%`
- `%EXACT_MODEL_NAME%`
- `%CUSTOM_MODEL_NAME%`
- `%FRIENDLY_TEXT_ENCODER_NAME%`
- `%CLEAN_FRIENDLY_TEXT_ENCODER_NAME%`
- `%EXACT_TEXT_ENCODER_NAME%`
- `%CUSTOM_TEXT_ENCODER_NAME%`

## Example Layouts

### Default

```text
%TOP_FOLDER%/%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

### No top folder

```text
%MODEL_NAME%/%TEXT_ENCODER_NAME%/%FILENAME%
```

### Exact model only

```text
%TOP_FOLDER%/%EXACT_MODEL_NAME%/%FILENAME%
```

### Include seed

```text
%MODEL_NAME%/%KSampler.seed%/%FILENAME%
```

### Include image size

```text
%MODEL_NAME%/%Empty Latent Image.width%x%Empty Latent Image.height%/%FILENAME%
```

### Include batch position and batch size

```text
%MODEL_NAME%/%BATCH_INDEX%-of-%BATCH_SIZE%/%FILENAME%
```

## `%node.widget%`

Examples:

- `%KSampler.seed%`
- `%Empty Latent Image.width%`
- `%Empty Latent Image.height%`

Before the first run, the helper preview shows these as `{node.widget}` because the real values only exist when the workflow executes.

After a successful run, the helper panel keeps a detection snapshot from the last execution. If you change layout-related widgets afterwards, the preview can still reuse those last detected model/text-encoder values until the next run refreshes them.

The helper now shows an explicit status badge:

- `Sample Preview` before the first real run
- `Fresh Detection` right after a run with current detected values
- `Last Detection Snapshot` after later edits, when the preview is still using the last known detection state

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

## Date And Time

You can choose between:

- `ComfyUI-style` with `%date:...%`
- `Python-style` with `%strftime:...%`

Recommended default:

```text
%date:yyyy-MM-dd_hh-mm-ss%
```

Example result:

```text
2026-04-22_21-22-05
```

### `%date:...%`

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
```

### `%strftime:...%`

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
## Workflow Metadata

`Export Workflow Metadata` controls whether PNG files store prompt and workflow metadata like the
normal ComfyUI `Save Image` node.

- `On`: saves prompt and workflow metadata into the PNG
- `Off`: writes a clean PNG without embedded workflow metadata

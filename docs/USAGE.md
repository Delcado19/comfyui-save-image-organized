# Usage

## Save Image Clean

`Save Image Clean` now follows one simple structure:

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
3. Pick `Friendly`, `Exact`, or `Custom` for `Model Name`
4. Pick `Friendly`, `Exact`, or `Custom` for `Text Encoder Name`
5. Leave `Filename` unchanged unless you want a different timestamp
6. Queue the workflow

Example result:

```text
portraits/flux 2 klein 9b [5K-M]/Lockout Qwen3 4b V2 [Her][q8]/2026-04-22_15-30-10.png
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
- `Exact`
- `Custom`

### Text Encoder Name

Controls what `%TEXT_ENCODER_NAME%` becomes.

Options:

- `Friendly`
- `Exact`
- `Custom`

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

## Useful Variables

### Main

- `%TOP_FOLDER%`
- `%MODEL_NAME%`
- `%TEXT_ENCODER_NAME%`
- `%FILENAME%`

### Detailed

- `%FRIENDLY_MODEL_NAME%`
- `%EXACT_MODEL_NAME%`
- `%CUSTOM_MODEL_NAME%`
- `%FRIENDLY_TEXT_ENCODER_NAME%`
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

## `%node.widget%`

Examples:

- `%KSampler.seed%`
- `%Empty Latent Image.width%`
- `%Empty Latent Image.height%`

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

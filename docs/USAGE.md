# Usage

## Save Image Clean

`Save Image Clean` supports two output strategies.

### 1. Legacy Mode

Leave `path_template` empty and provide:

- `model_folder`
- `clip_folder`
- `subfolder`
- `filename_datetime`

The resulting path is:

```text
<output_root>/<subfolder>/<model_folder>/<clip_folder>/<filename_datetime>.png
```

`filename_datetime` uses Python `strftime`, for example:

```text
%Y-%m-%d_%H-%M
```

### 2. Template Mode

Set `path_template` to generate the full relative output path.

Recommended template:

```text
%ACTIVE_UNET%/%ACTIVE_CLIP%/%date:yyyy-MM-dd_hh-mm%
```

Example result:

```text
jibMixZIT_v10/Huihui-Qwen3-4B-abliterated-v2.Q8_0/2026-04-21_14-37.png
```

## Template Variables

- `%ACTIVE_UNET%`: detected UNET loader name without a known model file extension
- `%ACTIVE_CLIP%`: detected CLIP loader name without a known model file extension
- `%MODEL_SHORT%`: shortened UNET name with common prefixes removed
- `%CLIP_SHORT%`: shortened CLIP name with common prefixes removed
- `%MODEL_FOLDER%`: manual `model_folder` fallback value without a known model file extension
- `%CLIP_FOLDER%`: manual `clip_folder` fallback value without a known model file extension
- `%SUBFOLDER%`: sanitized `subfolder` value

## Date Tokens

Inside `%date:...%`, these tokens are supported:

- `yyyy`
- `yy`
- `MM`
- `dd`
- `HH`
- `hh`
- `mm`
- `ss`

Example:

```text
%date:yyyy-MM-dd_hh-mm%
```

## Collision Modes

- `increment`: appends `-2`, `-3`, and so on
- `overwrite`: replaces an existing file
- `error`: raises an error if the path already exists
- `seconds`: retries with a timestamp that includes seconds

## Loader Detection Notes

Template mode traverses the upstream `prompt` graph from the current save node.

It currently favors:

- classes containing `UnetLoader`
- classes containing `ClipLoader`
- classes containing `CheckpointLoader` as fallback

If no loader name is found, the node falls back to the manual folder inputs.

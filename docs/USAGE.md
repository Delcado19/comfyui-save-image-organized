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

You can also combine custom variables with ComfyUI-style widget placeholders:

```text
%KSampler.seed%/%Empty Latent Image.width%x%Empty Latent Image.height%/%date:yyyy-MM-dd_hh-mm%
```

## Template Variables

- `%ACTIVE_UNET%`: detected UNET loader name without a known model file extension
- `%ACTIVE_CLIP%`: detected CLIP loader name without a known model file extension
- `%MODEL_SHORT%`: shortened UNET name with common prefixes removed
- `%CLIP_SHORT%`: shortened CLIP name with common prefixes removed
- `%MODEL_FOLDER%`: manual `model_folder` fallback value without a known model file extension
- `%CLIP_FOLDER%`: manual `clip_folder` fallback value without a known model file extension
- `%MODEL_DISPLAY%`: humanized active UNET name, using only the basename and a readable quant suffix when recognized
- `%CLIP_DISPLAY%`: humanized active CLIP name, using only the basename and a readable quant suffix when recognized
- `%MODEL_SELECTED%`: value chosen by the `model_source` dropdown or `model_custom_value`
- `%CLIP_SELECTED%`: value chosen by the `clip_source` dropdown or `clip_custom_value`
- `%SUBFOLDER%`: sanitized `subfolder` value

In practice this means:

- `ACTIVE_*`: auto-detected from the active workflow, then stripped of known model file extensions
- `*_SHORT`: based on the detected active name, but further shortened for cleaner output names
- `*_FOLDER`: taken from the manual node input fields, then stripped of known model file extensions

Example values:

- detected UNET loader name: `jibMixZIT_v10.safetensors`
- detected CLIP loader name: `mradermacher - Huihui-Qwen3-4B-abliterated-v2.Q8_0.gguf`
- manual `model_folder`: `manual-model`
- manual `clip_folder`: `manual-clip.gguf`
- `subfolder`: `portraits`

Resolved variables:

- `%ACTIVE_UNET%` -> `jibMixZIT_v10`
- `%ACTIVE_CLIP%` -> `mradermacher - Huihui-Qwen3-4B-abliterated-v2.Q8_0`
- `%MODEL_SHORT%` -> `jibMixZIT_v10`
- `%CLIP_SHORT%` -> `Huihui-Qwen3-4B-abliterated-v2.Q8_0`
- `%MODEL_FOLDER%` -> `manual-model`
- `%CLIP_FOLDER%` -> `manual-clip`
- `%MODEL_DISPLAY%` -> `jibMixZIT v10`
- `%CLIP_DISPLAY%` -> `Huihui Qwen3 4B abliterated v2 [8F]`
- `%SUBFOLDER%` -> `portraits`

Example template using only the manual folder fields:

```text
%SUBFOLDER%/%MODEL_FOLDER%/%CLIP_FOLDER%/%date:yyyy-MM-dd_hh-mm%
```

Example result:

```text
portraits/manual-model/manual-clip/2026-04-22_15-30.png
```

## Dropdown-Based Segment Selection

The node also provides `model_source` and `clip_source` dropdowns.

These let you choose which resolved value should be used for the model and clip path segments without having to write a template first.

Model source options:

- `MODEL_FOLDER`
- `ACTIVE_UNET`
- `MODEL_SHORT`
- `MODEL_DISPLAY`
- `CUSTOM`

Clip source options:

- `CLIP_FOLDER`
- `ACTIVE_CLIP`
- `CLIP_SHORT`
- `CLIP_DISPLAY`
- `CUSTOM`

When `CUSTOM` is selected, the node uses `model_custom_value` or `clip_custom_value`.

The chosen values are also exposed to templates as `%MODEL_SELECTED%` and `%CLIP_SELECTED%`.

## Search And Replace Placeholders

Template mode also supports ComfyUI-style `%node.widget%` placeholders.

Examples:

- `%KSampler.seed%`
- `%Empty Latent Image.width%`
- `%Empty Latent Image.height%`

Resolution is based on the execution prompt and can match:

- node title when present
- `Node name for S&R` when present
- node class name
- internal node id

If multiple nodes match the same name, the node raises an error so the template stays explicit.

## Date Tokens

Inside `%date:...%`, these ComfyUI-style tokens are supported:

- `M`
- `yyyy`
- `yy`
- `d`
- `MM`
- `dd`
- `h`
- `hh`
- `m`
- `mm`
- `s`
- `ss`

Example:

```text
%date:yyyy-MM-dd_hh-mm%
```

Unsupported text inside `%date:...%` remains unchanged.

## Strftime Tokens

Inside `%strftime:...%`, these directives are supported:

- `%Y`
- `%y`
- `%m`
- `%d`
- `%H`
- `%M`
- `%S`
- `%f`
- `%%`

Example:

```text
%strftime:%Y-%m-%d_%H-%M-%S%
```

This subset is intentionally small so behavior stays consistent across platforms.

## Collision Modes

- `increment`: appends `-2`, `-3`, and so on
- `overwrite`: replaces an existing file
- `error`: raises an error if the path already exists
- `seconds`: retries with a timestamp that includes seconds

## In-Node Help

`Save Image Clean` also exposes inline help in ComfyUI itself.

The node description and field tooltips explain:

- legacy mode versus template mode
- the difference between `ACTIVE_*`, `*_SHORT`, and `*_FOLDER`
- the purpose of `MODEL_DISPLAY`, `CLIP_DISPLAY`, `MODEL_SELECTED`, and `CLIP_SELECTED`
- how `model_folder`, `clip_folder`, and `subfolder` affect the final path
- which placeholder styles are supported in `path_template`
- the difference between `%date:...%` and `%strftime:...%`

The package also includes markdown-based node docs so the ComfyUI `Info` tab can show fuller help than the default generated table.

## Loader Detection Notes

Template mode traverses the upstream `prompt` graph from the current save node.

It currently favors:

- dedicated UNET loaders such as `UNETLoader`, `UnetLoaderGGUF`, and `Load Diffusion Model` style nodes
- dedicated CLIP or text encoder loaders such as `CLIPLoader`, `DualCLIPLoader`, `TripleCLIPLoader`, `QuadrupleCLIPLoader`, and `TextEncoderLoader` style nodes
- checkpoint loaders such as `CheckpointLoaderSimple`, `ImageOnlyCheckpointLoader`, and `unCLIPCheckpointLoader`
- custom loader nodes that use similar class names and input names for diffusion model or text encoder selection

If no loader name is found, the node falls back to the manual folder inputs.

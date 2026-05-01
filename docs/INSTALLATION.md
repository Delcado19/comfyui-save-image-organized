# Installation

## Comfy Registry

Recommended install:

```bash
comfy node install save-image-organized
```

The package is published in the Comfy Registry under:

- Publisher: `delcado`
- Node ID: `save-image-organized`
- Display name: `Save Image Organized`

After installation, restart ComfyUI if the node list does not refresh automatically.

## Manual Installation

1. Open your ComfyUI installation.
2. Go to `custom_nodes`.
3. Clone this repository into that directory:

```bash
git clone https://github.com/Delcado19/comfyui-save-image-organized.git comfyui-save-image-organized
```

4. Install the dependencies in the Python environment used by ComfyUI:

```bash
pip install -r requirements.txt
```

5. Restart ComfyUI.

## Existing Checkout

If the repository already exists locally, update it with:

```bash
git pull
```

Then restart ComfyUI so changed nodes are reloaded.

## Expected Result

After installation, ComfyUI should expose these nodes:

- `Save Image Organized`
- `Strip Model Extension`

# Installation

## Manual Installation

1. Open your ComfyUI installation.
2. Go to `custom_nodes`.
3. Clone this repository into that directory:

```bash
git clone <repo-url> comfyui-clean-save-nodes
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

- `Save Image Clean`
- `Strip Model Extension`

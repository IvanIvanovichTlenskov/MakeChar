# MakeChar - Project Context

## Project Overview

**MakeChar** is a browser extension for **Stable Diffusion WebUI** (Automatic1111). It adds a custom tab with a text input field to the WebUI interface, serving as a foundation for future character-related features.

### Architecture

- **Type**: Stable Diffusion WebUI Extension (Python/Gradio)
- **Main Component**: `scripts/makechar.py` - Defines the `MakeCharScript` class
- **UI Framework**: Gradio (used by Stable Diffusion WebUI)
- **Integration**: Uses `modules.scripts` and `modules.script_callbacks` from WebUI

### Key Components

| File | Purpose |
|------|---------|
| `scripts/makechar.py` | Main extension script with Gradio UI definition |
| `README.md` | Installation instructions and feature overview |

## Building and Running

### Prerequisites

- Stable Diffusion WebUI (Automatic1111) installed and running

### Installation

1. Open Stable Diffusion WebUI
2. Navigate to **Extensions** tab
3. Click **Install from URL**
4. Paste the repository URL
5. Click **Install**
6. Restart the WebUI server

### Development

The extension loads automatically when placed in the WebUI `extensions` directory. No separate build step is required.

```bash
# Typical WebUI startup (from parent WebUI directory)
./webui.sh    # Linux
webui-user.bat  # Windows
```

## Development Conventions

### Code Style

- **Class naming**: PascalCase for script classes (e.g., `MakeCharScript`)
- **Function naming**: snake_case for methods
- **Structure**: Follows Stable Diffusion WebUI extension pattern:
  - `title()` - Returns display name
  - `show()` - Determines visibility (img2img vs txt2img)
  - `ui()` - Builds Gradio interface
  - `run()` - Executes logic (currently a no-op placeholder)

### Extension Pattern

```python
class MyScript(scripts.Script):
    def title(self): ...      # Extension name
    def show(self, is_img2img): ...  # Visibility control
    def ui(self, is_img2img): ...    # Gradio UI components
    def run(self, p, *args): ...     # Processing logic
```

### Testing Practices

- Manual testing via WebUI interface
- Verify extension appears in expected tab
- Test input field functionality

## Current Features

- ✅ Text input field in a dedicated group
- ✅ Integrated into WebUI extension system
- 📝 Placeholder for future character generation features

## Notes for Future Development

- The `run()` method is currently a no-op (`pass`) - intended for future implementation
- The `text_field` component is returned from `ui()` but not yet processed
- Extension is marked as `AlwaysVisible` for both txt2img and img2img modes

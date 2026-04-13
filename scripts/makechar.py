import gradio as gr
import json
import os
import base64
from pathlib import Path
from PIL import Image
from modules import scripts, script_callbacks
import modules.shared as shared


# Constants
EXTENSION_DIR = Path(__file__).parent.parent
CHARACTERS_DIR = EXTENSION_DIR / "characters"
STYLE_FILE = EXTENSION_DIR / "style.css"
SLOTS_COUNT = 3


def ensure_characters_dir():
    """Ensure the characters directory exists."""
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)


def get_character_names():
    """Scan characters directory and return list of character names."""
    ensure_characters_dir()
    names = []
    for item in CHARACTERS_DIR.iterdir():
        if item.is_dir():
            data_file = item / "data.json"
            if data_file.exists():
                names.append(item.name)
    return sorted(names)


def load_character_data(char_name):
    """Load character data from JSON file."""
    char_dir = CHARACTERS_DIR / char_name
    data_file = char_dir / "data.json"
    
    if not data_file.exists():
        return None
    
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_character_data(char_name, slots_data):
    """Save character data to JSON file and save images."""
    char_dir = CHARACTERS_DIR / char_name
    char_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        "character_name": char_name,
        "slots": []
    }
    
    for i, slot in enumerate(slots_data):
        slot_data = {
            "image_path": None,
            "text": slot.get("text", "")
        }
        
        # Save image if provided
        img_data = slot.get("image")
        if img_data is not None:
            img_path = char_dir / f"slot_{i}.png"
            try:
                # img_data can be a PIL Image or a numpy array
                if isinstance(img_data, Image.Image):
                    img_data.save(img_path, "PNG")
                else:
                    # Convert numpy array to PIL Image
                    img = Image.fromarray(img_data)
                    img.save(img_path, "PNG")
                slot_data["image_path"] = str(img_path.relative_to(EXTENSION_DIR))
            except Exception as e:
                print(f"[MakeChar] Error saving image: {e}")
        
        data["slots"].append(slot_data)
    
    # Save JSON
    data_file = char_dir / "data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return True


def load_character_images(char_name):
    """Load images for a character."""
    char_dir = CHARACTERS_DIR / char_name
    images = []
    
    for i in range(SLOTS_COUNT):
        img_path = char_dir / f"slot_{i}.png"
        if img_path.exists():
            try:
                images.append(Image.open(img_path))
            except Exception:
                images.append(None)
        else:
            images.append(None)
    
    return images


def update_dropdown():
    """Update the character dropdown with available characters."""
    names = get_character_names()
    return gr.Dropdown(choices=names, value=names[0] if names else None)


class MakeCharScript(scripts.Script):
    def title(self):
        return "MakeChar"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        ensure_characters_dir()
        
        # State variables
        character_names = get_character_names()
        
        with gr.Group():
            # === 2.1. Верхняя панель (Управление персонажами) ===
            with gr.Row():
                with gr.Column(scale=2):
                    char_dropdown = gr.Dropdown(
                        label="Select Character",
                        choices=character_names,
                        value=character_names[0] if character_names else None,
                        interactive=True
                    )
                with gr.Column(scale=1):
                    new_btn = gr.Button("New", variant="secondary")
                with gr.Column(scale=1):
                    save_btn = gr.Button("Save", variant="primary")
            
            # === 2.2. Основная зона (Конструктор персонажа) ===
            # Three slots: each has image + text
            image_components = []
            text_components = []
            
            for i in range(SLOTS_COUNT):
                with gr.Row():
                    with gr.Column(scale=1):
                        img = gr.Image(
                            label=f"Slot {i + 1} Image",
                            type="pil",
                            sources=["upload", "clipboard"],
                            height=200
                        )
                        image_components.append(img)
                    with gr.Column(scale=1):
                        txt = gr.Textbox(
                            label=f"Slot {i + 1} Description",
                            placeholder=f"Describe attribute {i + 1} (e.g., hairstyle, clothing)...",
                            lines=3
                        )
                        text_components.append(txt)
            
            # === 2.3. Нижняя панель (Агрегатор промпта) ===
            with gr.Row():
                with gr.Column(scale=4):
                    final_prompt = gr.Textbox(
                        label="Combined Prompt",
                        placeholder="Combined prompt will appear here...",
                        lines=2,
                        interactive=True
                    )
                with gr.Column(scale=1):
                    send_btn = gr.Button("Send to Positive Prompt", variant="primary")
        
        # === Event Handlers ===
        
        # Auto-update combined prompt when any text field changes
        def combine_prompts(*texts):
            return " ".join(t for t in texts if t and t.strip())
        
        for txt in text_components:
            txt.change(
                fn=combine_prompts,
                inputs=text_components,
                outputs=final_prompt
            )
        
        # Load character data when dropdown selection changes
        def on_character_select(char_name):
            if not char_name:
                # Return empty values
                return [None] * SLOTS_COUNT + [""] * SLOTS_COUNT + [""]
            
            data = load_character_data(char_name)
            images = load_character_images(char_name)
            
            if data is None:
                return [None] * SLOTS_COUNT + [""] * SLOTS_COUNT + [""]
            
            slot_texts = []
            for i, slot in enumerate(data.get("slots", [])):
                slot_texts.append(slot.get("text", ""))
            
            # Fill remaining slots with empty strings
            while len(slot_texts) < SLOTS_COUNT:
                slot_texts.append("")
            
            # Combine prompts
            combined = combine_prompts(*slot_texts)
            
            return images + slot_texts + [combined]
        
        char_dropdown.change(
            fn=on_character_select,
            inputs=[char_dropdown],
            outputs=image_components + text_components + [final_prompt]
        )
        
        # New button - clear all fields
        def on_new_character():
            return [None] * SLOTS_COUNT + [""] * SLOTS_COUNT + [""] + [gr.Dropdown(value=None)]
        
        new_btn.click(
            fn=on_new_character,
            inputs=[],
            outputs=image_components + text_components + [final_prompt, char_dropdown]
        )
        
        # Save button - save current state
        def on_save_character(char_name, *args):
            images = args[:SLOTS_COUNT]
            texts = args[SLOTS_COUNT:SLOTS_COUNT * 2]
            
            if not char_name or not char_name.strip():
                return gr.update(), "Please enter a character name or select from dropdown"
            
            char_name = char_name.strip()
            
            slots_data = []
            for i in range(SLOTS_COUNT):
                slots_data.append({
                    "image": images[i],
                    "text": texts[i]
                })
            
            try:
                save_character_data(char_name, slots_data)
                # Update dropdown with new character
                new_choices = get_character_names()
                return (
                    gr.Dropdown(choices=new_choices, value=char_name),
                    f"Character '{char_name}' saved successfully!"
                )
            except Exception as e:
                return gr.update(), f"Error saving character: {str(e)}"
        
        save_btn.click(
            fn=on_save_character,
            inputs=[char_dropdown] + image_components + text_components,
            outputs=[char_dropdown, gr.Textbox(label="Status")]
        )
        
        # Send to Positive Prompt button - requires JavaScript
        send_btn.click(
            fn=lambda x: x,
            inputs=[final_prompt],
            outputs=[final_prompt],
            _js="sendToPositivePrompt"
        )

        # Return empty list to avoid "too many variables" error
        # The UI is already built and event handlers are registered
        return []

    def run(self, p, *args):
        pass


# JavaScript for sending prompt to main UI
def on_ui_tabs():
    # Load CSS
    css_content = ""
    if STYLE_FILE.exists():
        with open(STYLE_FILE, "r", encoding="utf-8") as f:
            css_content = f.read()
    
    js_code = """
<script>
function sendToPositivePrompt(promptText) {
    // Try to find the positive prompt textarea in txt2img tab
    const txt2imgPrompt = document.getElementById('txt2img_prompt');
    const img2imgPrompt = document.getElementById('img2img_prompt');
    
    let targetPrompt = null;
    
    // Check which tab is active or try txt2img first
    if (txt2imgPrompt && txt2imgPrompt.offsetParent !== null) {
        targetPrompt = txt2imgPrompt;
    } else if (img2imgPrompt && img2imgPrompt.offsetParent !== null) {
        targetPrompt = img2imgPrompt;
    } else if (txt2imgPrompt) {
        targetPrompt = txt2imgPrompt;
    }
    
    if (targetPrompt) {
        targetPrompt.value = promptText;
        // Trigger input event to update Gradio state
        targetPrompt.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    return promptText;
}
</script>
"""
    return js_code + f"<style>{css_content}</style>", "MakeChar", "MakeChar"


# Register the JavaScript and CSS
script_callbacks.on_ui_tabs(on_ui_tabs)

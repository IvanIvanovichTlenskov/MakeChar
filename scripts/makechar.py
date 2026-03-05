import gradio as gr
from modules import scriptscripts, script_callbacks


class MakeCharScript(scriptscripts.Script):
    def title(self):
        return "MakeChar"

    def show(self, is_img2img):
        return scriptscripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Row():
                with gr.Column(scale=4):
                    text_field = gr.Textbox(
                        label="Text Input",
                        placeholder="Enter text here...",
                        lines=3
                    )
        return [text_field]

    def run(self, p, text_field=None):
        pass

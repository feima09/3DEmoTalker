# WebUI by mrfakename <X @realmrfakename / HF @mrfakename>
# Demo also available on HF Spaces: https://huggingface.co/spaces/mrfakename/MeloTTS
import gradio as gr
import os, torch, io
# os.system('python -m unidic download')
print("Make sure you've downloaded unidic (python -m unidic download) for this WebUI to work.")
from melo.api import TTS
speed = 1.0
import tempfile
import click

device = 'auto'
models = {
        'default': TTS(language='ZH_MIX_EN', device=device, 
                      config_path='D:\\MeloTTS-main\\weights\\threehz\\config.json', 
                      ckpt_path='D:\\MeloTTS-main\\weights\\threehz\\G_6000.pth'),
    }
speaker_ids = models['default'].hps.data.spk2id

default_text_dict = {
    'default': '你好，我叫光小明，是光明实验室研发的智能AI助手。',
}


def synthesize(speaker, text, speed, language, progress=gr.Progress()):
    bio = io.BytesIO()
    models[language].tts_to_file(text, models[language].hps.data.spk2id[speaker], bio, speed=speed, pbar=progress.tqdm,
                                 format='wav')
    return bio.getvalue()


def load_speakers(language, text):
    if language not in models:
        language = 'default'  # 回退到默认模型
    if text.strip() in default_text_dict.values():
        newtext = default_text_dict.get(language, default_text_dict['default'])
    else:
        newtext = text
    return gr.update(
        value=list(models[language].hps.data.spk2id.keys())[0],
        choices=list(models[language].hps.data.spk2id.keys())
    ), newtext


with gr.Blocks() as demo:
    gr.Markdown('# MeloTTS WebUI\n\nA WebUI for MeloTTS.')
    with gr.Group():
        speaker = gr.Dropdown(speaker_ids.keys(), interactive=True, value='EN-US', label='Speaker')
        language = gr.Radio(['default'], label='Language', value='default')
        speed = gr.Slider(label='Speed', minimum=0.1, maximum=10.0, value=1.0, interactive=True, step=0.1)
        text = gr.Textbox(label="Text to speak", value=default_text_dict['EN'])
        language.input(load_speakers, inputs=[language, text], outputs=[speaker, text])
    btn = gr.Button('Synthesize', variant='primary')
    aud = gr.Audio(interactive=False)
    btn.click(synthesize, inputs=[speaker, text, speed, language], outputs=[aud])
    gr.Markdown('WebUI by [mrfakename](https://twitter.com/realmrfakename).')


@click.command()
@click.option('--share', '-s', is_flag=True, show_default=True, default=False,
              help="Expose a publicly-accessible shared Gradio link usable by anyone with the link. Only share the link with people you trust.")
@click.option('--host', '-h', default=None)
@click.option('--port', '-p', type=int, default=None)
def main(share, host, port):
    demo.queue(api_open=False).launch(show_api=False, share=True, server_name=host, server_port=port)


if __name__ == "__main__":
    main()

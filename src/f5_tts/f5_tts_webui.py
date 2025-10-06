import random
import sys
import gradio as gr 
import tempfile
import torchaudio
import soundfile as sf
from cached_path import cached_path
import argparse
import torch
from deep_translator import GoogleTranslator

from f5_tts.infer.utils_infer import (
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
    remove_silence_for_generated_wav,
    save_spectrogram,
    transcribe
)
from f5_tts.model import DiT
from f5_tts.model.utils import seed_everything
from f5_tts.cleantext.th_normalize import normalize_text
from f5_tts.infer.infer_gradio import *

#ถ้าอยากใช้โมเดลที่อัพเดทใหม หรือโมเดลภาษาอื่น สามารถแก้ไขโค้ด Model และ Vocab เช่น default_model_base = "hf://VIZINTZOR/F5-TTS-THAI/model_350000.pt"
default_model_base = "hf://VIZINTZOR/F5-TTS-THAI/model_1000000.pt"
v2_model_base = "hf://VIZINTZOR/F5-TTS-TH-v2/model_250000.pt"
vocab_base = "./vocab/vocab.txt"
vocab_ipa_base = "./vocab/vocab_ipa.txt"

model_choices = ["Default", "V2", "Custom"]

global f5tts_model
f5tts_model = None

def load_f5tts(ckpt_path, vocab_path=vocab_base, model_type="v1"):
    if model_type == "v1":
        F5TTS_model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, text_mask_padding=False, conv_layers=4, pe_attn_head=1)
    elif model_type == "v2":
        F5TTS_model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, text_mask_padding=True, conv_layers=4, pe_attn_head=None)
        vocab_path = "./vocab/vocab_ipa.txt"
    model = load_model(DiT, F5TTS_model_cfg, ckpt_path, vocab_file = vocab_path, use_ema=True)
    print(f"Loaded model from {ckpt_path}")
    return model

vocoder = load_vocoder()

f5tts_model = load_f5tts(str(cached_path(default_model_base)))

def update_custom_model(selected_model):
    return gr.update(visible=selected_model == "Custom")
    
def update_v2_ipa(model):
    return gr.update(value="IPA" if model == "V2" else "Default")
    
def load_custom_model(model_choice,model_custom_path):
    torch.cuda.empty_cache()
    global f5tts_model
    model_path = default_model_base if model_choice == "Default" else v2_model_base
    if model_choice == "Custom":
        f5tts_model = load_f5tts(str(cached_path(model_custom_path)))
        return f"Loaded Custom Model {model_custom_path}"
    else:
        f5tts_model = load_f5tts(
            str(cached_path(model_path)),
            vocab_path = vocab_ipa_base if model_choice == "V2" else vocab_base,
            model_type = "v2" if model_choice == "V2" else "v1"
        )
        return f"Loaded Model {model_choice}"
    
def infer_tts(
    ref_audio_orig,
    ref_text,
    gen_text,
    remove_silence=True,
    cross_fade_duration=0.15,
    nfe_step=32,
    speed=1,
    cfg_strength=2,
    max_chars=250,
    seed=-1,
    lang_process="Default"
):
    global f5tts_model
    if f5tts_model is None:
        f5tts_model = load_f5tts(str(cached_path(default_model_base)))

    if seed == -1:
        seed = random.randint(0, sys.maxsize)
    seed_everything(seed)
    output_seed = seed

    if not ref_audio_orig:
        gr.Warning("Please provide reference audio.")
        return gr.update(), gr.update(), ref_text, output_seed

    if not gen_text.strip():
        gr.Warning("Please enter text to generate.")
        return gr.update(), gr.update(), ref_text, output_seed
    
    ref_audio, ref_text = preprocess_ref_audio_text(ref_audio_orig, ref_text)
    
    gen_text_cleaned = normalize_text(gen_text)

    final_wave, final_sample_rate, combined_spectrogram = infer_process(
        ref_audio,
        ref_text,
        gen_text_cleaned,
        f5tts_model,
        vocoder,
        cross_fade_duration=float(cross_fade_duration),
        nfe_step=nfe_step,
        speed=speed,
        progress=gr.Progress(),
        cfg_strength=cfg_strength,
        set_max_chars=max_chars,
        use_ipa=True if lang_process == "IPA" else False
    )

    if remove_silence:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            sf.write(f.name, final_wave, final_sample_rate)
            remove_silence_for_generated_wav(f.name)
            final_wave, _ = torchaudio.load(f.name)
        final_wave = final_wave.squeeze().cpu().numpy()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_spectrogram:
        spectrogram_path = tmp_spectrogram.name
        save_spectrogram(combined_spectrogram, spectrogram_path)
    
    print("seed:", output_seed)
    return (final_sample_rate, final_wave), spectrogram_path, ref_text, output_seed 

def translate(text=str,target="th"):
    translated = GoogleTranslator(source='auto', target=target).translate(text=text)
    print("Translated Text:",translated)
    return translated

def transcribe_text(input_audio="",is_translate=False,target_lg="th",source_lg='th'):
    if is_translate:
        output_text = translate(text=transcribe(input_audio=input_audio,language=source_lg),target=target_lg)
    else:
        output_text = transcribe(input_audio=input_audio,language=source_lg)
    return output_text

def create_gradio_interface():
    with gr.Blocks(title="F5-TTS ภาษาไทย 🇹🇭",theme=gr.themes.Ocean()) as demo:
        gr.Markdown("# F5-TTS ภาษาไทย")
        gr.Markdown("สร้างคำพูดจากข้อความ ด้วย Zero-shot TTS หรือ เสียงต้นฉบับ ภาษาไทย.")

        with gr.Row():
            model_select = gr.Radio(
                label="โมเดล",
                choices=model_choices,
                value="Default",
                interactive=True,
            )
            model_custom = gr.Textbox(label="ตำแหน่งโมเดลแบบกำหนดเอง",value="hf://VIZINTZOR/F5-TTS-THAI/model_650000.pt", visible=False, interactive=True)
            model_status = gr.Textbox(label="สถานะโมเดล", value="")
            load_custom_btn = gr.Button("โหลด⭮",variant="primary")
    
        with gr.Tab(label="Text To Speech"):      
            with gr.Row():
                with gr.Column():
                    ref_text = gr.Textbox(label="ข้อความต้นฉบับ", lines=1, info="แนะนำให้ใช้เสียงที่มีความยาวไม่เกิน 5-10 วินาที")
                    ref_audio = gr.Audio(label="เสียงต้นฉบับ", type="filepath")
                    gen_text = gr.Textbox(label="ข้อความที่จะสร้าง", lines=4)
                    generate_btn = gr.Button("🚀สร้าง",variant="primary")

                    with gr.Accordion(label="⚙️ตั้งค่า"):
                        lang_input = gr.Radio(label="การประมวลผลข้อความภาษา",choices=["Default","IPA"],value="Default",info="IPA สำหรับโมเดล V2 เท่านั้น")
                        remove_silence = gr.Checkbox(label="Remove Silence", value=True)
                        speed = gr.Slider(label="ความเร็ว", value=1, minimum=0.3, maximum=1.5, step=0.1)
                        cross_fade_duration = gr.Slider(label="Cross Fade Duration", value=0.15, minimum=0, maximum=1, step=0.05)
                        nfe_step = gr.Slider(label="NFE Step", value=32, minimum=7, maximum=64, step=1, info="ยิ่งค่ามากยิ่งมีคุณภาพสูง แต่อาจจะช้าลง")
                        cfg_strength = gr.Slider(label="CFG Strength", value=2, minimum=1, maximum=4, step=0.1)
                        max_chars = gr.Number(label="ตัวอักษรสูงสุดต่อส่วน", minimum=50, maximum=1000, value=300,
                                            info="จำนวนตัวอักษรสูงสุดที่ใช้ในการแบ่งส่วน สำหรับข้อความยาวๆ")
                        seed = gr.Number(label="Seed", value=-1, precision=0, info="-1 = สุ่ม Seed")
                        
                with gr.Column():
                    output_audio = gr.Audio(label="เสียงที่สร้าง", type="filepath")
                    seed_output = gr.Textbox(label="Seed", interactive=False)
                    
            gr.Examples(
                examples=[
                    [
                        "./src/f5_tts/infer/examples/thai_examples/ref_gen_1.wav",
                        "ได้รับข่าวคราวของเราที่จะหาที่มันเป็นไปที่จะจัดขึ้น.",
                        "พรุ่งนี้มีประชุมสำคัญ อย่าลืมเตรียมเอกสารให้เรียบร้อย"
                    ],
                    [
                        "./src/f5_tts/infer/examples/thai_examples/ref_gen_2.wav",
                        "ฉันเดินทางไปเที่ยวที่จังหวัดเชียงใหม่ในช่วงฤดูหนาวเพื่อสัมผัสอากาศเย็นสบาย.",
                        "ฉันชอบฟังเพลงขณะขับรถ เพราะช่วยให้รู้สึกผ่อนคลาย"
                    ],
                    [
                        "./src/f5_tts/infer/examples/thai_examples/ref_gen_3.wav",
                        "กู้ดอาฟเต้อนูนไนท์ทูมีทยู.",
                        "วันนี้อากาศดีมาก เหมาะกับการไปเดินเล่นที่สวนสาธารณะ"
                    ],
                    [
                        "./src/f5_tts/infer/examples/thai_examples/ref_gen_4.wav",
                        "เราอยากจะตื่นขึ้นมามั้ยคะ.",
                        "เมื่อวานฉันไปเดินเล่นที่ชายหาด เสียงคลื่นซัดฝั่งเป็นจังหวะที่ชวนให้ใจสงบ."
                    ]
                ],
                inputs=[ref_audio, ref_text, gen_text],
                fn=infer_tts,
                cache_examples=False,
                label="ตัวอย่าง"
            )
            
            gr.Markdown("# คำแนะนำ")
            gr.Markdown(
                        """ - สามารถตั้งค่า "ตัวอักษรสูงสุดต่อส่วน" หรือ max_chars เพื่อลดความผิดพลาดการอ่าน แต่ความเร็วในการสร้างจะช้าลง สามารถปรับลด NFE Step เพื่อเพิ่มความเร็วได้
                        ปรับ NFE Step เหลือ 7 สามารถเพิ่มความเร็วการในการสร้างได้มาก แต่เสียงที่ได้พอฟังได้.
                        - อย่าลืมเว้นวรรคประโยคเพื่อให้สามารถแบ่งส่วนในการสร้างได้.
                        - สำหรับ ref_text หรือ ข้อความตันฉบับ แนะนำให้ใช้เป็นภาษาไทยหรือคำอ่านภาษาไทยสำหรับเสียงภาษาอื่น เพื่อให้การอ่านภาษาไทยดีขึ้น เช่น Good Morning > กู้ดมอร์นิ่ง.
                        - สำหรับเสียงต้นแบบ ควรใช้ความยาวไม่เกิน 10 วินาที ถ้าเป็นไปได้ห้ามมีเสียงรบกวน.
                        - สามารถปรับลดความเร็วให้ช้าลง ถ้าเสียงต้นฉบับมีความยาวไม่มาก เช่น 2-5 วินาที
                        - การอ่านข้อความยาวๆ หรือบางคำ ยังไม่ถูกต้อง สามารถปรับลดความเร็วเพื่อให้การอ่านถูกต้องได้ เช่น ถ้าเสียงต้นฉบับมีความยาว 1-3 วินาที อาจจะต้องประความเร็วเหลือ 0.8-0.9.
                        - โมเดลตอนนี้ยังเน้นการอ่านภาษาไทยเป็นหลัก การอ่านภาษาไทยผสมกับภาษาอังกฤษยังต้องปรับปรุง.
                    """
            )

            load_custom_btn.click(
                fn=load_custom_model,
                inputs=[
                    model_select,
                    model_custom
                    ],
                outputs=model_status
            )
            
            model_select.change(
                fn=update_custom_model,
                inputs=model_select,
                outputs=model_custom
            )
            
            model_select.change(
                fn=update_v2_ipa,
                inputs=model_select,
                outputs=lang_input
            )
            
            generate_btn.click(
                fn=infer_tts,
                inputs=[
                    ref_audio,
                    ref_text,
                    gen_text,
                    remove_silence,
                    cross_fade_duration,
                    nfe_step,
                    speed,
                    cfg_strength,
                    max_chars,
                    seed,
                    lang_input
                ],
                outputs=[
                    output_audio,
                    gr.Image(label="Spectrogram",visible=False),
                    ref_text,
                    seed_output
                ]
            )
            
        with gr.Tab(label="Multi Speech"):
            with gr.Row():
                gr.Markdown(
                    """
                    **ตัวอย่าง:**                                                                      
                    {ปกติ} สวัสดีครับ มีอะไรให้ผมช่วยไหมครับ    
                    {เศร้า} ผมเครียดจริงๆ นะตอนนี้...      
                    {โกรธ} รู้ไหม! เธอไม่ควรอยู่ที่นี่!       
                    {กระซิบ} ฉันมีอะไรจะบอกคุณ แต่มันเป็นความลับนะ.   
                    """
                )
            gr.Markdown(
                """อัปโหลดคลิปเสียงที่แตกต่างกันสำหรับแต่ละประเภทคำพูด โดยประเภทคำพูดแรกเป็นประเภทที่จำเป็นต้องมี คุณสามารถเพิ่มประเภทคำพูดเพิ่มเติมได้โดยคลิกปุ่ม "เพิ่มประเภทคำพูด"."""
            )

            # Regular speech type (mandatory)
            with gr.Row() as regular_row:
                with gr.Column():
                    regular_name = gr.Textbox(value="ปกติ", label="ลักษณะอารมณ์/ชื่อผู้พูด")
                    regular_insert = gr.Button("เพิ่มตัวกำกับ", variant="secondary")
                regular_audio = gr.Audio(label="เสียงต้นแบบ", type="filepath")
                regular_ref_text = gr.Textbox(label="ข้อความต้นฉบับ", lines=2)

            # Regular speech type (max 100)
            max_speech_types = 100
            speech_type_rows = [regular_row]
            speech_type_names = [regular_name]
            speech_type_audios = [regular_audio]
            speech_type_ref_texts = [regular_ref_text]
            speech_type_delete_btns = [None]
            speech_type_insert_btns = [regular_insert]

            # Additional speech types (99 more)
            for i in range(max_speech_types - 1):
                with gr.Row(visible=False) as row:
                    with gr.Column():
                        name_input = gr.Textbox(label="ลักษณะอารมณ์/ชื่อผู้พูด")
                        delete_btn = gr.Button("ลบ", variant="secondary")
                        insert_btn = gr.Button("เพิ่มตัวกำกับ", variant="secondary")
                    audio_input = gr.Audio(label="เสียงตัวอย่าง", type="filepath")
                    ref_text_input = gr.Textbox(label="ข้อความต้นฉบับ", lines=2)
                speech_type_rows.append(row)
                speech_type_names.append(name_input)
                speech_type_audios.append(audio_input)
                speech_type_ref_texts.append(ref_text_input)
                speech_type_delete_btns.append(delete_btn)
                speech_type_insert_btns.append(insert_btn)

            # Button to add speech type
            add_speech_type_btn = gr.Button("เพิ่มประเภทคำพูด",variant="secondary")

            # Keep track of autoincrement of speech types, no roll back
            speech_type_count = 1

            # Function to add a speech type
            def add_speech_type_fn():
                row_updates = [gr.update() for _ in range(max_speech_types)]
                global speech_type_count
                if speech_type_count < max_speech_types:
                    row_updates[speech_type_count] = gr.update(visible=True)
                    speech_type_count += 1
                else:
                    gr.Warning("Exhausted maximum number of speech types. Consider restart the app.")
                return row_updates

            add_speech_type_btn.click(add_speech_type_fn, outputs=speech_type_rows)

            # Function to delete a speech type
            def delete_speech_type_fn():
                return gr.update(visible=False), None, None, None

            # Update delete button clicks
            for i in range(1, len(speech_type_delete_btns)):
                speech_type_delete_btns[i].click(
                    delete_speech_type_fn,
                    outputs=[speech_type_rows[i], speech_type_names[i], speech_type_audios[i], speech_type_ref_texts[i]],
                )

            # Text input for the prompt
            gen_text_input_multistyle = gr.Textbox(
                label="ข้อความ",
                lines=10,
                placeholder="""ป้อนสคริปต์โดยใส่ชื่อผู้พูด (หรือลักษณะอารมณ์) ไว้ที่ต้นแต่ละบล็อก ตัวอย่างเช่น:
                {ปกติ} สวัสดีครับ มีอะไรให้ผมช่วยไหมครับ
                {เศร้า} ผมเครียดจริงๆ นะตอนนี้...
                {โกรธ} รู้ไหม! เธอไม่ควรอยู่ที่นี่!
                {กระซิบ} ฉันมีอะไรจะบอกคุณ แต่มันเป็นความลับนะ.""",
            )

            def make_insert_speech_type_fn(index):
                def insert_speech_type_fn(current_text, speech_type_name):
                    current_text = current_text or ""
                    speech_type_name = speech_type_name or "None"
                    updated_text = current_text + f"{{{speech_type_name}}} "
                    return updated_text

                return insert_speech_type_fn

            for i, insert_btn in enumerate(speech_type_insert_btns):
                insert_fn = make_insert_speech_type_fn(i)
                insert_btn.click(
                    insert_fn,
                    inputs=[gen_text_input_multistyle, speech_type_names[i]],
                    outputs=gen_text_input_multistyle,
                )

            with gr.Accordion("⚙️ตั้งค่า", open=False):
                remove_silence_multistyle = gr.Checkbox(
                    label="Remove Silences",
                    value=True,
                )
                ms_use_ipa = gr.Checkbox(label="การประมวลผลข้อความภาษา(IPA)", value=False, info="ใช้ IPA สำหรับโมเดล V2 เท่านั้น")
                ms_cross_fade_duration = gr.Slider(label="Cross Fade Duration", value=0.15, minimum=0, maximum=1, step=0.05)
                ms_nfe_step = gr.Slider(label="NFE Step", value=32, minimum=7, maximum=64, step=1, info="ยิ่งค่ามากยิ่งมีคุณภาพสูง แต่จะช้าลง")


            # Generate button
            generate_multistyle_btn = gr.Button("🚀สร้าง", variant="primary")

            # Output audio
            audio_output_multistyle = gr.Audio(label="เสียงที่สร้าง")

            def generate_multistyle_speech(
                gen_text,
                cross_fade_duration,
                nfe_step,
                lang_process,
                *args,
            ):
                speech_type_names_list = args[:max_speech_types]
                speech_type_audios_list = args[max_speech_types : 2 * max_speech_types]
                speech_type_ref_texts_list = args[2 * max_speech_types : 3 * max_speech_types]
                remove_silence = args[3 * max_speech_types]
                # Collect the speech types and their audios into a dict
                speech_types = OrderedDict()

                ref_text_idx = 0
                for name_input, audio_input, ref_text_input in zip(
                    speech_type_names_list, speech_type_audios_list, speech_type_ref_texts_list
                ):
                    if name_input and audio_input:
                        speech_types[name_input] = {"audio": audio_input, "ref_text": ref_text_input}
                    else:
                        speech_types[f"@{ref_text_idx}@"] = {"audio": "", "ref_text": ""}
                    ref_text_idx += 1

                # Parse the gen_text into segments
                segments = parse_speechtypes_text(gen_text)

                # For each segment, generate speech
                generated_audio_segments = []
                current_style = "Regular"

                for segment in segments:
                    style = segment["style"]
                    text = segment["text"]

                    if style in speech_types:
                        current_style = style
                    else:
                        gr.Warning(f"Type {style} is not available, will use Regular as default.")
                        current_style = "Regular"

                    try:
                        ref_audio = speech_types[current_style]["audio"]
                    except KeyError:
                        gr.Warning(f"Please provide reference audio for type {current_style}.")
                        return [None] + [speech_types[style]["ref_text"] for style in speech_types]
                    ref_text = speech_types[current_style].get("ref_text", "")

                    ms_cleaned_text = normalize_text(text)
                    # Generate speech for this segment
                    audio_out, _, ref_text_out = infer(
                        ref_audio, 
                        ref_text, 
                        ms_cleaned_text, 
                        f5tts_model, 
                        vocoder, 
                        remove_silence, 
                        cross_fade_duration=cross_fade_duration, 
                        nfe_step=nfe_step, 
                        show_info=print,
                        use_ipa=lang_process,
                    )  # show_info=print no pull to top when generating
                    sr, audio_data = audio_out

                    generated_audio_segments.append(audio_data)
                    speech_types[current_style]["ref_text"] = ref_text_out

                # Concatenate all audio segments
                if generated_audio_segments:
                    final_audio_data = np.concatenate(generated_audio_segments)
                    return [(sr, final_audio_data)] + [speech_types[style]["ref_text"] for style in speech_types]
                else:
                    gr.Warning("No audio generated.")
                    return [None] + [speech_types[style]["ref_text"] for style in speech_types]

            generate_multistyle_btn.click(
                generate_multistyle_speech,
                inputs=[
                    gen_text_input_multistyle,
                    ms_cross_fade_duration,
                    ms_nfe_step,
                    ms_use_ipa    
                ]
                + speech_type_names
                + speech_type_audios
                + speech_type_ref_texts
                + [
                    remove_silence_multistyle,
                ],
                outputs=[audio_output_multistyle] + speech_type_ref_texts,
            )

            # Validation function to disable Generate button if speech types are missing
            def validate_speech_types(gen_text, regular_name, *args):
                speech_type_names_list = args

                # Collect the speech types names
                speech_types_available = set()
                if regular_name:
                    speech_types_available.add(regular_name)
                for name_input in speech_type_names_list:
                    if name_input:
                        speech_types_available.add(name_input)

                # Parse the gen_text to get the speech types used
                segments = parse_speechtypes_text(gen_text)
                speech_types_in_text = set(segment["style"] for segment in segments)

                # Check if all speech types in text are available
                missing_speech_types = speech_types_in_text - speech_types_available

                if missing_speech_types:
                    # Disable the generate button
                    return gr.update(interactive=False)
                else:
                    # Enable the generate button
                    return gr.update(interactive=True)

            gen_text_input_multistyle.change(
                validate_speech_types,
                inputs=[gen_text_input_multistyle, regular_name] + speech_type_names,
                outputs=generate_multistyle_btn,
            )

        with gr.Tab(label="Speech to Text"):
            gr.Markdown("เปลี่ยนเสียงพูดเป็นข้อความด้วย โมเดล [Whisper](https://github.com/openai/whisper) โดยใช้ [faster-whisper](https://github.com/SYSTRAN/faster-whisper)")
            with gr.Row():
                with gr.Column():
                    ref_audio_input = gr.Audio(label="เสียงต้นฉบับ",type="filepath")
                    is_translate = gr.Checkbox(label="แปลภาษา")
                    generate_btn_stt = gr.Button("ถอดข้อความ",variant="primary")

                    with gr.Accordion(label="ตั้งค่า",open=False):
                        source_lg = gr.Dropdown(label="ภาษาต้นฉบับ",choices=["Auto",'th',"en"],value="Auto")
                        target_lg = gr.Dropdown(label="ภาษาที่แปล",choices=['th',"en"],value="th")

                with gr.Column():
                    output_ref_text = gr.Textbox(label="ข้อความต้นฉบับ",lines=3,show_copy_button=True)
            
            generate_btn_stt.click(fn=transcribe_text,
                                   inputs=[ref_audio_input,is_translate,target_lg,source_lg],
                                   outputs=output_ref_text)
            
        return demo

def main():
    parser = argparse.ArgumentParser(description="Share Link")
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    demo = create_gradio_interface()
    demo.launch(inbrowser=True, share=args.share)

if __name__ == "__main__":
    main()





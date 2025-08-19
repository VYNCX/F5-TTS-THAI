# F5-TTS: A Fairytaler that Fakes Fluent and Faithful Speech with Flow Matching. Support For Thai language.

[![python](https://img.shields.io/badge/Python-3.10-brightgreen)](https://github.com/SWivid/F5-TTS)
[![arXiv](https://img.shields.io/badge/arXiv-2410.06885-b31b1b.svg?logo=arXiv)](https://arxiv.org/abs/2410.06885)
[![lab](https://img.shields.io/badge/X--LANCE-Lab-grey?labelColor=lightgrey)](https://x-lance.sjtu.edu.cn/)
[![lab](https://img.shields.io/badge/Peng%20Cheng-Lab-grey?labelColor=lightgrey)](https://www.pcl.ac.cn)
<!-- <img src="https://github.com/user-attachments/assets/12d7749c-071a-427c-81bf-b87b91def670" alt="Watermark" style="width: 40px; height: auto"> -->

Text-to-Speech (TTS) ภาษาไทย — เครื่องมือสร้างเสียงพูดจากข้อความด้วยเทคนิค Flow Matching ด้วยโมเดล F5-TTS

โมเดล Finetune : [VIZINTZOR/F5-TTS-THAI](https://huggingface.co/VIZINTZOR/F5-TTS-THAI) 

โมเดล Finetune V2 (IPA) : [VIZINTZOR/F5-TTS-TH-V2](https://huggingface.co/VIZINTZOR/F5-TTS-TH-V2)

 - การอ่านข้อความยาวๆ หรือบางคำ ยังไม่ถูกต้อง

# การติดตั้ง
ก่อนเริ่มใช้งาน ต้องติดตั้ง:
 - Python (แนะนำเวอร์ชัน 3.10 ขึ้นไป)
 - [CUDA](https://developer.nvidia.com/cuda-downloads) แนะนำ CUDA version 12.8
 - [eSpeak NG](https://github.com/espeak-ng/espeak-ng)
```sh
git clone https://github.com/VYNCX/F5-TTS-THAI.git
cd F5-TTS-THAI
python -m venv venv
call venv/scripts/activate
pip install git+https://github.com/VYNCX/F5-TTS-THAI.git

#จำเป็นต้องติดตั้งเพื่อใช้งานได้มีประสิทธิภาพกับ GPU
pip install torch==2.7.0+cu128 torchaudio==2.7.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
```
หรือ รันไฟล์ `install.bat` เพื่อติดตั้ง

# การใช้งาน
สามารถรันไฟล์ `app-webui.bat` เพื่อใช้งานได้ 
```sh
  python src/f5_tts/f5_tts_webui.py
```
หรือ 

```sh
  f5-tts_webui
```
ใช้งานบน [Google Colab](https://colab.research.google.com/drive/10yb4-mGbSoyyfMyDX1xVF6uLqfeoCNxV?usp=sharing)

คำแนะนำ :
- สามารถตั้งค่า "ตัวอักษรสูงสุดต่อส่วน" หรือ max_chars เพื่อลดความผิดพลาดการอ่าน แต่ความเร็วในการสร้างจะช้าลง สามารถปรับลด NFE Step เพื่อเพิ่มความเร็วได้.
- อย่าลืมเว้นวรรคประโยคเพื่อให้สามารถแบ่งส่วนในการสร้างได้.
- สำหรับ ref_text หรือ ข้อความตันฉบับ แนะนำให้ใช้เป็นภาษาไทยหรือคำอ่านภาษาไทยสำหรับเสียงภาษาอื่น เพื่อให้การอ่านภาษาไทยดีขึ้น เช่น Good Morning > กู้ดมอร์นิ่ง.
- สำหรับเสียงต้นแบบ ควรใช้ความยาวไม่เกิน 8 วินาที ถ้าเป็นไปได้ห้ามมีเสียงรบกวน.
- สามารถปรับลดความเร็ว เพื่อให้การอ่านคำดีขึ้นได้ เช่น ความเร็ว 0.8-0.9 เพื่อลดการอ่านผิดหรือคำขาดหาย แต่ลดมากไปอาจมีเสียงต้นฉบับแทรกเข้ามา.
  
  <details><summary>ตัวอย่าง WebUI</summary>
  
   - Text To Speech
   ![Example_Gradio#3](https://github.com/user-attachments/assets/9fd6bf42-3c34-41aa-8f88-3f7ea191e4f0)
  
   - Multi Speech
   ![Example_Gradio#4](https://github.com/user-attachments/assets/fc57b2d0-bef9-4454-94c3-b72ca2551265)
 
  
# ฝึกอบรม และ Finetune
ใช้งานบน Google Colab [Finetune](https://colab.research.google.com/drive/1jwzw4Jn1qF8-F0o3TND68hLHdIqqgYEe?usp=sharing) หรือ 

ติดตั้ง

```sh
  cd F5-TTS-THAI
  pip install -e .
```

เปิด Gradio
```sh
  f5-tts_finetune-gradio
```

# ตัวอย่างเสียง

- เสียงต้นฉบับ
- ข้อความ : ได้รับข่าวคราวของเราที่จะหาที่มันเป็นไปที่จะจัดขึ้น.
  
https://github.com/user-attachments/assets/003c8a54-6f75-4456-907d-d28897e4c393

- เสียงที่สร้าง 1(ข้อความเดียวกัน)
- ข้อความ : ได้รับข่าวคราวของเราที่จะหาที่มันเป็นไปที่จะจัดขึ้น.
   
https://github.com/user-attachments/assets/926829f2-8d56-4f0f-8e2e-d73cfcecc511

- เสียงที่สร้าง 2(ข้อความใหม่)
- ข้อความ : ฉันชอบฟังเพลงขณะขับรถ เพราะช่วยให้รู้สึกผ่อนคลาย

https://github.com/user-attachments/assets/06d6e94b-5f83-4d69-99d1-ad19caa9792b

# อ้างอิง

- [F5-TTS](https://github.com/SWivid/F5-TTS)











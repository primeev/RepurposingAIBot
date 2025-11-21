import os
import uuid
import shutil
import random
import zipfile
from moviepy.editor import *
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")  # Railway will inject this

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a video and I'll make 150+ unique variants that bypass TikTok/Instagram duplicate detection!\n\n"
        "Max 2 minutes recommended."
    )

def randomize_video(input_path, output_path):
    clip = VideoFileClip(input_path)
    duration = clip.duration

    if random.random() > 0.5:
        crop_factor = random.uniform(0.92, 0.99)
        w, h = clip.size
        clip = clip.crop(x_center=w/2, y_center=h/2, width=w*crop_factor, height=h*crop_factor).resize((w, h))

    clip = clip.fx(vfx.colorx, factor=random.uniform(0.85, 1.15))
    if random.random() > 0.3:
        clip = clip.fx(vfx.gamma_corr, random.uniform(0.9, 1.1))

    speed = random.uniform(0.95, 1.05)
    clip = clip.fx(vfx.speedx, speed)

    if random.random() > 0.7:
        clip = clip.fx(vfx.mirror_x)
    if random.random() > 0.5:
        clip = clip.fx(vfx.vignette, radius=1.3)

    new_w = clip.w + random.choice([-2, 0, 2, 4])
    new_h = clip.h + random.choice([-2, 0, 2, 4])
    clip = clip.resize((new_w, new_h))

    if clip.audio:
        audio = clip.audio.fx(afx.volumex, random.uniform(0.9, 1.1))
        if random.random() > 0.5:
            pitch = random.uniform(0.94, 1.06)
            audio = audio.fx(afx.speedx, pitch)  # pitch shift via speed on audio only
        clip = clip.set_audio(audio)

    clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="veryfast", threads=os.cpu_count() or 4, verbose=False, logger=None)
    clip.close()

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Downloading your video...")
    video_file = await update.message.video.get_file()
    input_path = f"temp_{uuid.uuid4()}.mp4"
    await video_file.download_to_drive(input_path)
    await msg.edit_text("Generating 150 unique variants… (usually 5–12 minutes)")

    variants_dir = f"outputs/{uuid.uuid4()}"
    os.makedirs(variants_dir, exist_ok=True)
    num_variants = 150

    for i in range(num_variants):
        output_path = os.path.join(variants_dir, f"variant_{i+1}.mp4")
        randomize_video(input_path, output_path)
        if (i+1) % 25 == 0:
            await msg.edit_text(f"Generated {i+1}/{num_variants}…")

    zip_path = f"{variants_dir}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(variants_dir):
            for f in files:
                zf.write(os.path.join(root, f), f)

    await msg.edit_text("Uploading ZIP with all variants…")
    await update.message.reply_document(open(zip_path, "rb"), caption=f"Here are your {num_variants} unique variants!")

    shutil.rmtree(variants_dir)
    os.remove(zip_path)
    os.remove(input_path)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()

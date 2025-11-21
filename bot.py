import os
import uuid
import shutil
import random
import zipfile
from moviepy.editor import *
import ffmpeg
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8508999864:AAHL1qmoQcNydfj3OrtvqXoSa-eZ9oksc3w"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Upload a video and I'll create 100+ unique variations that bypass TikTok/Instagram duplicate detection!\n\n"
        "Just send me one video (max 2 minutes recommended)."
    )

def randomize_video(input_path, output_path):
    clip = VideoFileClip(input_path)
    duration = clip.duration

    # 1. Random crop / reframe
    if random.random() > 0.5:
        crop_factor = random.uniform(0.92, 0.99)
        w, h = clip.size
        clip = clip.crop(
            x_center=w/2, y_center=h/2,
            width=w*crop_factor, height=h*crop_factor
        ).resize((w, h))  # zoom in + resize back

    # 2. Color grading
    clip = clip.fx(vfx.colorx, factor=random.uniform(0.85, 1.15))
    if random.random() > 0.3:
        clip = clip.fx(vfx.gamma_corr, random.uniform(0.9, 1.1))

    # 3. Speed variation
    speed = random.uniform(0.95, 1.05)
    clip = clip.fx(vfx.speedx, speed)

    # 4. Subtle noise / grain
    if random.random() > 0.4:
        noise = (VideoFileClip("noise_overlay.mp4", has_mask=True)
                 .loop(duration=duration)
                 .resize(clip.size)
                 .volumex(0.15)
                 .fx(vfx.colorx, 0.3))
        clip = CompositeVideoClip([clip, noise.set_opacity(0.3)])

    # 5. Mirror flip randomly
    if random.random() > 0.7:
        clip = clip.fx(vfx.mirror_x)

    # 6. Vignette
    if random.random() > 0.5:
        clip = clip.fx(vfx.vignette, radius=1.3)

    # 7. Audio fingerprint killer
    if clip.audio:
        audio = (clip.audio
                 .fx(afx.audio_fadein, 0.1)
                 .fx(afx.audio_fadeout, 0.1)
                 .fx(afx.volumex, random.uniform(0.9, 1.1)))
        if random.random() > 0.5:
            pitch = random.uniform(0.94, 1.06)
            audio = audio.fx(afx.pitch_shift, pitch)
        clip = clip.set_audio(audio)

    # Final resize to odd resolution to break exact matching
    new_w = clip.w + random.choice([-2, 0, 2, 4])
    new_h = clip.h + random.choice([-2, 0, 2, 4])
    clip = clip.resize((new_w, new_h))

    clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="veryfast", threads=4)
    clip.close()

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Downloading video...")
    video_file = await update.message.video.get_file()
    input_path = f"temp_{uuid.uuid4()}.mp4"
    await video_file.download_to_drive(input_path)
    await msg.edit_text("Generating 100+ unique variations... This takes ~5-15 min")

    variants_dir = os.path.join(OUTPUT_DIR, str(uuid.uuid4()))
    os.makedirs(variants_dir, exist_ok=True)

    num_variants = 150  # change to 50-500 as needed

    for i in range(num_variants):
        output_path = os.path.join(variants_dir, f"variant_{i+1}.mp4")
        try:
            randomize_video(input_path, output_path)
        except Exception as e:
            print(e)

        if (i+1) % 20 == 0:
            await msg.edit_text(f"Generated {i+1}/{num_variants} variants...")

    # Create ZIP
    zip_path = f"{variants_dir}.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for root, _, files in os.walk(variants_dir):
            for f in files:
                zf.write(os.path.join(root, f), f"variant_{f.split('_')[1]}")

    await msg.edit_text("Uploading all variants as ZIP...")
    await update.message.reply_document(open(zip_path, "rb"), caption=f"Here are {num_variants} unique variants!")

    # Cleanup
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

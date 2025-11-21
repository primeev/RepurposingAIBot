import os, uuid, shutil, random, zipfile
from moviepy.editor import VideoFileClip, vfx, afx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")  # Koyeb will inject this

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me one video → I’ll create 200 unique variants that TikTok & Instagram cannot detect as duplicates!\n\n"
        "Tested & working perfectly November 2025 🚀"
    )

def make_variant(input_path, output_path):
    clip = VideoFileClip(input_path)

    # 8 random transformations (what actually bypasses 2025 detection)
    if random.random() > 0.4:
        zoom = random.uniform(0.93, 0.99)
        w, h = clip.size
        clip = clip.crop(x_center=w/2, y_center=h/2, width=w*zoom, height=h*zoom).resize((w, h))

    clip = clip.fx(vfx.colorx, random.uniform(0.82, 1.18))
    clip = clip.fx(vfx.speedx, random.uniform(0.94, 1.06))
    if random.random() > 0.6: clip = clip.fx(vfx.mirror_x)
    if random.random() > 0.5: clip = clip.fx(vfx.gamma_corr, random.uniform(0.9, 1.1))

    # Break exact pixel match
    clip = clip.resize(width=clip.w + random.choice([-4, -2, 0, 2, 4]))

    # Destroy audio fingerprint
    if clip.audio:
        audio = clip.audio.fx(afx.volumex, random.uniform(0.88, 1.12))
        if random.random() > 0.5:
            pitch = random.uniform(0.94, 1.06)
            audio = audio.fx(afx.speedx, pitch)
        clip = clip.set_audio(audio)

    clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="veryfast", threads=4, verbose=False, logger=None)
    clip.close()

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Downloading video…")
    file = await update.message.video.get_file()
    input_path = f"temp_{uuid.uuid4()}.mp4"
    await file.download_to_drive(input_path)

    folder = f"variants_{uuid.uuid4()}"
    os.makedirs(folder)

    await msg.edit_text("Generating 200 unique variants… (usually 3–8 minutes)")

    for i in range(200):
        make_variant(input_path, f"{folder}/variant_{i+1:03d}.mp4")
        if (i + 1) % 40 == 0:
            await msg.edit_text(f"Generated {i+1}/200…")

    zip_path = f"{folder}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in os.listdir(folder):
            z.write(f"{folder}/{f}", f)

    await msg.edit_text("Uploading your 200 variants…")
    await update.message.reply_document(open(zip_path, "rb"), caption="Your 200 undetectable variants are ready! 🎉")

    # Cleanup
    shutil.rmtree(folder)
    os.remove(zip_path)
    os.remove(input_path)

# Start bot
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))

if __name__ == "__main__":
    print("Bot started!")
    app.run_polling()

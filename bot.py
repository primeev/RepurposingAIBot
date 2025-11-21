import os, uuid, shutil, random, zipfile
from moviepy.editor import VideoFileClip, vfx, afx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("KOYEB_PUBLIC_URL")  # Koyeb auto-sets this

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send one video → get 200 TikTok/Instagram-safe unique variants instantly! 🚀")

def make_variant(in_path, out_path):
    clip = VideoFileClip(in_path)
    if random.random() > 0.4:
        zoom = random.uniform(0.93, 0.99)
        w, h = clip.size
        clip = clip.crop(x_center=w/2, y_center=h/2, width=w*zoom, height=h*zoom).resize((w, h))
    clip = clip.fx(vfx.colorx, random.uniform(0.82, 1.18)).fx(vfx.speedx, random.uniform(0.94, 1.06))
    if random.random() > 0.6: clip = clip.fx(vfx.mirror_x)
    if random.random() > 0.5: clip = clip.fx(vfx.gamma_corr, random.uniform(0.9, 1.1))
    clip = clip.resize(width=clip.w + random.choice([-4,-2,0,2,4]))
    if clip.audio:
        audio = clip.audio.fx(afx.volumex, random.uniform(0.88, 1.12))
        if random.random() > 0.5:
            audio = audio.fx(afx.speedx, random.uniform(0.94, 1.06))
        clip = clip.set_audio(audio)
    clip.write_videofile(out_path, codec="libx264", audio_codec="aac", preset="veryfast", threads=4, verbose=False, logger=None)
    clip.close()

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Downloading…")
    file = await update.message.video.get_file()
    in_path = f"temp_{uuid.uuid4()}.mp4"
    await file.download_to_drive(in_path)
    folder = f"variants_{uuid.uuid4()}"
    os.makedirs(folder)
    await msg.edit_text("Creating 200 unique variants…")

    for i in range(200):
        make_variant(in_path, f"{folder}/v{i+1:03d}.mp4")
        if (i+1) % 40 == 0:
            await msg.edit_text(f"Generated {i+1}/200…")

    zip_path = f"{folder}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in os.listdir(folder):
            z.write(f"{folder}/{f}", f)

    await msg.edit_text("Uploading ZIP…")
    await update.message.reply_document(open(zip_path, "rb"), caption="Your 200 unique variants! 🎉")

    shutil.rmtree(folder)
    os.remove(zip_path)
    os.remove(in_path)

# Webhook handler (required for Koyeb)
async def webhook(request):
    update = Update.de_json(await request.json(), app.bot)
    await app.process_update(update)
    return web.Response()

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))

# Health check endpoint
async def health(request):
    return web.Response(text="OK")

if __name__ == "__main__":
    web_app = web.Application()
    web_app.router.add_post(f"/{TOKEN}", webhook)
    web_app.router.add_get("/", health)
    
    port = int(os.getenv("PORT", 8080))
    print(f"Bot starting on port {port}…")
    web.run_app(web_app, host="0.0.0.0", port=port)

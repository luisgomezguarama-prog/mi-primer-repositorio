import asyncio
import discord
from discord.ext import commands
import yt_dlp as youtube_dl

# ==============================================
# ⚙️ CONFIGURACIÓN DEL BOT
# ==============================================
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", description="🎵 Bot musical con yt_dlp actualizado", intents=intents)

# ==============================================
# 🔧 CONFIGURACIÓN DE yt_dlp Y FFMPEG
# ==============================================
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extract_flat': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'noplaylist': True,
    'default_search': 'auto',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


# ==============================================
# 🎧 FUNCIÓN PARA EXTRAER AUDIO DE YOUTUBE
# ==============================================
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


# ==============================================
# 🤖 EVENTO ON_READY
# ==============================================
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print("------")


# ==============================================
# 📡 CONECTARSE AUTOMÁTICAMENTE AL CANAL DE VOZ
# ==============================================
@bot.command()
async def join(ctx):
    """Hace que el bot se una al canal de voz del usuario."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"🎙️ Conectado al canal: **{channel.name}**")
        else:
            await ctx.voice_client.move_to(channel)
            await ctx.send(f"🔄 Movido al canal: **{channel.name}**")
    else:
        await ctx.send("❌ No estás conectado a ningún canal de voz.")


# ==============================================
# 🎶 REPRODUCIR AUDIO DE YOUTUBE
# ==============================================
@bot.command()
async def play(ctx, *, url):
    """Reproduce una canción desde YouTube (stream directo)."""
    if not ctx.author.voice:
        return await ctx.send("❌ Debes estar en un canal de voz para usar este comando.")

    # Conectarse automáticamente
    if ctx.voice_client is None:
        await ctx.author.voice.channel.connect()

    voice_client = ctx.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        voice_client.play(player, after=lambda e: print(f'Error: {e}') if e else None)
    await ctx.send(f"🎵 Reproduciendo: **{player.title}**")


# ==============================================
# ⏸️ COMANDOS DE CONTROL
# ==============================================
@bot.command()
async def pause(ctx):
    """Pausa la música."""
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("⏸️ Música pausada.")
    else:
        await ctx.send("❌ No hay música reproduciéndose.")

@bot.command()
async def resume(ctx):
    """Reanuda la música pausada."""
    vc = ctx.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("▶️ Música reanudada.")
    else:
        await ctx.send("❌ No hay música pausada.")

@bot.command()
async def stop(ctx):
    """Detiene la música."""
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("⏹️ Música detenida.")
    else:
        await ctx.send("❌ No hay música reproduciéndose.")

@bot.command()
async def leave(ctx):
    """Desconecta el bot del canal de voz."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Me desconecté del canal de voz.")
    else:
        await ctx.send("❌ No estoy conectado a ningún canal de voz.")


# ==============================================
# 🔊 AJUSTAR VOLUMEN
# ==============================================
@bot.command()
async def volume(ctx, vol: int):
    """Cambia el volumen del reproductor (0–100)."""
    vc = ctx.voice_client
    if vc and vc.source:
        vc.source.volume = vol / 100
        await ctx.send(f"🔊 Volumen ajustado a **{vol}%**")
    else:
        await ctx.send("❌ No hay música reproduciéndose.")


# ==============================================
# 🚀 INICIO DEL BOT
# ==============================================
bot.run("TuToken")

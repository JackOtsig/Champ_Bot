import os, re, asyncio, youtube_dl, discord, math, datetime
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='-',intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio[ext=m4a]/best[ext=m4a]',
    'default_search': 'auto',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        }]
    }
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source,volume)
        self.data = data
        self.title = data.get('title')
        self.url = ''
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

playlist = []
settings = {'loopType' : 'None'} #None, Queue, Track
start_time = datetime.datetime.now()
skipb = False

@bot.command()
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if type(voice_client) == type(None):
        await ctx.send("I am not in a voice channel!")
        return
    if ctx.message.author.voice:
        if voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send("I'm not in a voice channel!")
    else:
        await ctx.send("You must be in a voice channel to do this")
#youtube\.[a-zA-Z]+/wINFO\?v\[
    #regex for youtube url
@bot.command()
async def play(ctx, *, url):
    global settings, playlist, start_time
    index = 0
    YDL_OPTIONS = {'format': 'bestaudio', 'default_search': 'auto', 'noplaylist' : True}
    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    if type(ctx.message.author.voice) == type(None):
        await ctx.send("You must be in a voice channel to do this")
        return
    channel = ctx.message.author.voice.channel
    try:
        await channel.connect()
    except:
        pass
    voice = bot.voice_clients
    for vc in voice:
        if vc.channel == channel:
            voice = vc
            break
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
    URL = info['entries'][0]['formats'][0]['url']
    rematch = re.search("dur=([+-]?(?=\.\d|\d)(?:\d+)?(?:\.?\d*))(?:[eE]([+-]?\d+))?", URL)
    dur = rematch.group()[4:]
    duration = int(math.ceil(float(dur)))
    name = info['entries'][0]['title']
    playlist.append([URL, duration, name])
    if len(playlist) > 0:
        pldur = int(playlist[index][1] - (datetime.datetime.now() - start_time).total_seconds())
        for i in range(index + 1, len(playlist) - 1):
            pldur = pldur + playlist[i][1]
        hours = int(pldur/3600)
        minutes = int((pldur%3600)/60)
        seconds = int(pldur%60)
        playlist_duration = ('0'+str(hours))[-2:]+':'+('0'+str(minutes))[-2:]+':'+('0'+str(seconds))[-2:]
        await ctx.send(name+' added to queue! Playing in:'+str(playlist_duration))
    if not voice.is_playing() and len(playlist) == 1:
        await ctx.send('Bot is playing')
        while True:
            try:
                voice.play(discord.FFmpegPCMAudio(playlist[index][0], **FFMPEG_OPTIONS))
                start_time = datetime.datetime.now()
            except:
                playlist = []
                await ctx.send("Couldn't play the song!")
                break
            if settings['loopType'] != 'Track' and len(playlist) != 1:
                await ctx.send('Now Playing: '+playlist[index][2])
            for i in range(1,playlist[index][1]):
                global skipb
                await asyncio.sleep(1)
                if skipb:
                    voice.stop()
                    skipb = False
                    break
            if settings['loopType'] != 'Track':
                index += 1
                if index == len(playlist):
                    if settings['loopType'] == 'Queue':
                        index = 0
                    else:
                        playlist = []
                        await ctx.send('Queue Cleared!')
                        break
    return

@bot.command()
async def loop(ctx):
    global settings
    if settings['loopType'] == 'Queue':
        settings['loopType'] = 'Track'
        await ctx.send('Looping Track')
    elif settings['loopType'] == 'Track':
        settings['loopType'] = 'None'
        await ctx.send('Looping Disabled')
    elif settings['loopType'] == 'None':
        settings['loopType'] = 'Queue'
        await ctx.send('Looping Queue')

@bot.command()
async def clear(ctx):
    global playlist
    playlist = []
    await leave(ctx)
    await ctx.send('Queue Cleared!')

@bot.command()
async def queue(ctx):
    que = ''
    pldur = 0
    for i in range(0, len(playlist)):
        pldur = pldur + playlist[i][1]
    hours = int(pldur/3600)
    minutes = int((pldur%3600)/60)
    seconds = int(pldur%60)
    for au in playlist:
        que = que+au[2]+'      '+str(au[1])+'\n'
    if que:
        await ctx.send(que)
    await ctx.send(('0'+str(hours))[-2:]+':'+('0'+str(minutes))[-2:]+':'+('0'+str(seconds))[-2:])

@bot.command()
async def skip(ctx):
    global skipb
    skipb = True

if __name__ == "__main__":
    bot.run(TOKEN)

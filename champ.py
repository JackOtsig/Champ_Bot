import os
import discord
from dotenv import load_dotenv
from discord.ext import commands,tasks
import youtube_dl
import asyncio
import pathlib
#sets the path variable to where champ.py is stored
path = str(pathlib.Path(__file__).parent.resolve())
#sets the videos variable to the path to the videos folder
videos = path+'/videos'
#loads the .env file (local variables)
load_dotenv()
#loads the bots token from the .env
TOKEN = os.getenv('DISCORD_TOKEN')
#declares intent; basicaly special bot perms
intents = discord.Intents.all()
#the actual bot object
bot = commands.Bot(command_prefix='-',intents=intents)
#settings for the youtube download
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

@bot.command(name='stop', help='To make the bot leave the voice channel')
async def leave(ctx):
    #voice client = the server contextually, object of the "voice client" (not sure if that is every channel or what?)
    voice_client = ctx.message.guild.voice_client
    #checks if bot is connected to any channel
    if voice_client.is_connected():
        #disconnects
        await voice_client.disconnect()
        #checks if the message author is in voice or not
    if not ctx.message.author.voice:
        #returns this if not
        await ctx.send("You must be in a voice channel to do this")
    else:
        #if bot isn't connected to a channel it returns an error
        await ctx.send("The bot is not connected to a voice channel.")
@bot.command(name='play', help='To play a song')
async def play(ctx,url):
    #if the message author is not in voice
    if not ctx.message.author.voice:
        #gives an error
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        #exits
        return
    #gets the voice channel of the user
    channel = ctx.message.author.voice.channel
    print(channel)
    #gets the voice client as an object
    voice_client = ctx.message.guild.voice_client
    #if there is no voice client
    if voice_client == None:
        #await voice client
        await channel.connect()
           #else LOL
    else:
        #moves to users channel
        await voice_client.move_to(channel)
    try :
        #in a way activates the bots "singing" capabilities
        voice_channel = ctx.message.guild.voice_client
        #makes the bot do the typing thing
        async with ctx.typing():
            print('filename')
            #changes to the videos directory
            os.chdir(videos)
            #downloads the video and saves the name as the filename variable                        * not working, partially downloading but not finishing
            filename = await YTDLSource.from_url(url, loop=None, stream=True)
            playlist.append(filename)
            print(f'{filename} done')
            #plays that bih                                                                         * never worked, doesnt play them
            while len(playlist) > 0:
                await voice_channel.play(discord.FFmpegPCMAudio(str(playlist[0])))
                voice_client.play(discord.FFmpegPCMAudio(song_info["formats"][0]["url"]))
                voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
                voice_client.source.volume = 1
                playlist.pop(0)
            #returns to the main directory
            os.chdir(path)
            print('now playing!')
        #tells users what song is playing
        await ctx.send('**Now playing:** {} ~'.format(filename))
        #UNLESS
    except:
        #it's not connected to a voice channel lol
        await ctx.send("The bot is not connected to a voice channel.")

if __name__ == "__main__":
    bot.run(TOKEN)
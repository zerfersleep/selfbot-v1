import discord
from discord.ext import commands
import asyncio
import random
import time
import json
import aiohttp
import sys

TOKEN = "Enter your bot token here."
PREFIX = "!" # Enter prefix bot

kiss_list = [
    "https://cdn.discordapp.com/attachments/1508018446024048750/1510571945496805386/ee029d939113f7e7e7986d9d681c6f9a.gif"
]

hug_list = [
    "https://cdn.discordapp.com/attachments/1508018446024048750/1510571945828028426/3daa34205381fc84833a1508baf5111d.gif"
]

start_time = time.time()
voice_tasks = {}
nhay_tasks = {}
nhay_start_time = {}

def read_messages(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []
        
GATEWAY_URL = "wss://gateway.discord.gg/?v=9&encoding=json"

bot = commands.Bot(command_prefix=PREFIX, self_bot=True)

async def identify_payload(token: str):
    return {
        "op": 2,
        "d": {
            "token": token,
            "capabilities": 61,
            "properties": {
                "os": "Windows",
                "browser": "Discord Client",
                "device": "",
                "system_locale": "en-US",
                "browser_user_agent": "Discord/1.0",
                "browser_version": "1.0",
                "os_version": "10",
                "referrer": "",
                "referring_domain": "",
                "referrer_current": "",
                "referring_domain_current": "",
                "release_channel": "stable",
                "client_build_number": 9999,
                "client_event_source": None,
            },
            "presence": {
                "status": "online",
                "since": 0,
                "activities": [{
                    "name": "Zerfer Sleep",
                    "type": 1,
                    "url": "https://twitch.tv/fake_streamer"
                }],
                "afk": False,
            },
            "compress": False,
        },
    }

async def voice_state_update(guild_id: str, channel_id: str):
    return {
        "op": 4,
        "d": {
            "guild_id": guild_id,
            "channel_id": channel_id,
            "self_mute": True,
            "self_deaf": True,
            "self_video": True,
            "self_stream": True,
        }
    }

async def send_heartbeat(ws, interval: float, last_seq):
    while True:
        await asyncio.sleep(interval)
        if ws.closed:
            break
        seq = last_seq[0] if last_seq[0] is not None else None
        await ws.send_json({"op": 1, "d": seq})

async def keep_alive(ws, guild_id, channel_id):
    while not ws.closed:
        await asyncio.sleep(45)
        try:
            await ws.send_json(await voice_state_update(guild_id, channel_id))
        except Exception:
            break

async def voice_connect(token: str, guild_id: str, channel_id: str, task_id: str):
    last_seq = [None]
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(GATEWAY_URL) as ws:
                    heartbeat_task = None
                    keepalive_task = None
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            op = data.get('op')
                            t = data.get('t')
                            s = data.get('s')

                            if s is not None:
                                last_seq[0] = s

                            if op == 10:
                                interval = data['d']['heartbeat_interval'] / 1000
                                if heartbeat_task:
                                    heartbeat_task.cancel()
                                heartbeat_task = asyncio.create_task(send_heartbeat(ws, interval, last_seq))
                                await ws.send_json(await identify_payload(token))

                            elif t == "READY":
                                await ws.send_json(await voice_state_update(guild_id, channel_id))
                                if keepalive_task:
                                    keepalive_task.cancel()
                                keepalive_task = asyncio.create_task(keep_alive(ws, guild_id, channel_id))

                            elif t == "VOICE_STATE_UPDATE":
                                print(f"[Voice] Đã vào voice channel {channel_id}")

                            elif op == 9:
                                break

                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
                    
                    if heartbeat_task:
                        heartbeat_task.cancel()
                    if keepalive_task:
                        keepalive_task.cancel()
                        
        except Exception as e:
            print(f"[Voice] Lỗi: {e}")
        
        await asyncio.sleep(5)

@bot.event
async def on_ready():
    print(f"[+] Logged in as {bot.user}")
    print(f"[+] Prefix: {PREFIX}")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.message.edit(content=f"Độ trễ của bot là **{latency}ms**")

@bot.command()
async def uptime(ctx):
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    await ctx.message.edit(content=f"{hours} giờ {minutes} phút {seconds} giây")

@bot.command()
async def say(ctx, *, text):
    await ctx.message.edit(content=text)

@bot.command()
async def kiss(ctx, member: discord.Member = None):
    await ctx.message.delete()
    if member is None:
        member = ctx.author
    gif = random.choice(kiss_list)
    await ctx.send(f"# Hôn em yêu {member.mention} một cái. 💋\n{gif}")

@bot.command()
async def hug(ctx, member: discord.Member = None):
    await ctx.message.delete()
    if member is None:
        member = ctx.author
    gif = random.choice(hug_list)
    await ctx.send(f"# Ôm bé {member.mention} cái nà. 🤗\n{gif}")

@bot.command()
async def menu(ctx):
    await ctx.message.delete()
    await ctx.send(f"""
```
☆ Zerfer Selfbot Command
Version 1.0.2
------------------------------
Tổng lệnh bot: 12
Các lệnh hiện có:

{PREFIX}menu - xem chức năng của bot
{PREFIX}ping - kiểm tra độ trễ
{PREFIX}uptime - thời gian hoạt động
{PREFIX}say - bot nói lại
{PREFIX}kiss @user - hôn người khác
{PREFIX}hug @user - ôm người khác
{PREFIX}voice <id_kênh> - vào voice channel
{PREFIX}leave - rời voice channel
{PREFIX}nhay <delay> @user- spam nhây
{PREFIX}stopnhay - dừng nhây ở kênh hiện tại
{PREFIX}tasknhay - xem task nhây đang chạy
{PREFIX}restart - khởi động lại bot
------------------------------
Prefix: {PREFIX}
Bot by Zerfer
```
""")

@bot.command()
async def voice(ctx, channel_id: int):
    await ctx.message.delete()
    task_id = str(ctx.guild.id)
    
    if task_id in voice_tasks:
        await ctx.send("Đã ở trong voice channel rồi!", delete_after=2)
        return
    
    task = asyncio.create_task(voice_connect(TOKEN, str(ctx.guild.id), str(channel_id), task_id))
    voice_tasks[task_id] = task
    await ctx.send(f"Đang vào voice channel <#{channel_id}>...", delete_after=3)

@bot.command()
async def leave(ctx):
    await ctx.message.delete()
    task_id = str(ctx.guild.id)
    
    if task_id in voice_tasks:
        voice_tasks[task_id].cancel()
        del voice_tasks[task_id]
        
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
        
        await ctx.send("Đã rời voice channel!", delete_after=2)
    else:
        await ctx.send("Không ở trong voice channel nào!", delete_after=2)

@bot.command()
async def nhay(ctx, delay: float, *, mentions: str = None):
    await ctx.message.delete()
    channel_id = ctx.channel.id
    
    if channel_id in nhay_tasks:
        await ctx.send("Đã có nhây đang chạy ở kênh này!", delete_after=2)
        return
    
    messages = read_messages('nhay.txt')
    if not messages:
        await ctx.send("File nhay.txt trống hoặc không tồn tại!", delete_after=2)
        return
    
    mentioned_users = []
    if mentions:
        for word in mentions.split():
            if word.startswith('<@') and word.endswith('>'):
                user_id = word.replace('<@', '').replace('>', '').replace('!', '')
                user = ctx.guild.get_member(int(user_id))
                if user:
                    mentioned_users.append(user.mention)
    
    nhay_start_time[channel_id] = time.time()
    
    async def nhay_task():
        try:
            while True:
                for msg in messages:
                    if not nhay_tasks.get(channel_id):
                        return
                    content = msg
                    if mentioned_users:
                        content = f"{msg} {' '.join(mentioned_users)}"
                    await ctx.send(content)
                    await asyncio.sleep(delay)
        except asyncio.CancelledError:
            pass
    
    task = asyncio.create_task(nhay_task())
    nhay_tasks[channel_id] = task
    await ctx.send(f"Bắt đầu nhây với delay {delay}s", delete_after=2)

@bot.command()
async def stopnhay(ctx):
    await ctx.message.delete()
    channel_id = ctx.channel.id
    
    if channel_id in nhay_tasks:
        nhay_tasks[channel_id].cancel()
        del nhay_tasks[channel_id]
        if channel_id in nhay_start_time:
            del nhay_start_time[channel_id]
        await ctx.send("Đã dừng nhây ở kênh này!", delete_after=2)
    else:
        await ctx.send("Không có nhây nào đang chạy ở kênh này!", delete_after=2)

@bot.command()
async def tasknhay(ctx):
    await ctx.message.delete()
    
    if not nhay_tasks:
        await ctx.send("Không có task nhay nào đang chạy!")
        return
    
    result = "**Danh sách task nhây:**\n```\n"
    for channel_id, task in nhay_tasks.items():
        channel = bot.get_channel(channel_id)
        channel_name = channel.name if channel else str(channel_id)
        if channel_id in nhay_start_time:
            elapsed = int(time.time() - nhay_start_time[channel_id])
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            result += f"ID Kênh: {channel_id} ({channel_name})\nThời gian: {hours} giờ {minutes} phút {seconds} giây\n\n"
        else:
            result += f"ID Kênh: {channel_id} ({channel_name})\n\n"
    
    result += "```"
    await ctx.send(result)

@bot.command()
async def restart(ctx):
    await ctx.message.delete()
    await ctx.send("***Đang khởi động lại bot***", delete_after=2)
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)
    
bot.run(TOKEN)
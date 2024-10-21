import os
import django
import discord
from discord import app_commands
from discord.ext import commands
import environ
from datetime import datetime
from asyncio import sleep as s

# โหลด environment variables จากไฟล์ .env
env = environ.Env()
environ.Env.read_env()

# ตั้งค่า Django Settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from accounts.models import DiscordProfile

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('/help'))
    print(f"{bot.user.name} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="hello", description="ทักทาย Hello World!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello World!")

@bot.tree.command(name="invite", description="รับลิงก์เชิญบอท KuBot")
async def invite(interaction: discord.Interaction):
    # สร้าง Embed สำหรับการเชิญ
    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        description="KuBot เป็นวิธีที่สะดวกในการจัดการการเรียนของคุณ",
        title="เชิญฉันเข้าสู่เซิร์ฟเวอร์ของคุณ คลิกที่นี่!"
    )
    
    # เพิ่มข้อมูลผู้เขียนใน Embed
    embed.set_author(
        name="KuBot",
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        icon_url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    # เพิ่ม Thumbnail
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    # ส่ง Embed ไปยังผู้ใช้
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ping", description="ตรวจสอบ ping ของบอท")
async def ping(interaction: discord.Interaction):
    # คำนวณความหน่วงของบอท
    bot_latency = round(bot.latency * 1000, 2)

    # สร้าง Embed เพื่อนำเสนอผลลัพธ์
    embed = discord.Embed(
        title="🏓 Pong!",
        description="เช็คสถานะ Ping ของบอท",
        color=discord.Color.dark_teal()
    )
    
    # เพิ่มข้อมูล latency
    embed.add_field(name="Latency:", value=f"`{bot_latency}` ms", inline=False)

    # ส่ง Embed ไปยัง Discord
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="ดู Avatar ของผู้ใช้")
@app_commands.describe(member="สมาชิกที่ต้องการดู Avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    if member is None:
        member = interaction.user
    embed = discord.Embed(title=f"{member}'s Avatar", color=discord.Color.dark_teal())
    embed.set_image(url=member.avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="profile", description="ดูโปรไฟล์ของผู้ใช้")
@app_commands.describe(user="สมาชิกที่ต้องการดูโปรไฟล์")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user
    embed = discord.Embed(color=discord.Color.dark_teal())
    embed.set_thumbnail(url=user.avatar)
    embed.set_author(name=user.name)
    embed.add_field(name="Mention:", value=user.mention, inline=True)
    embed.add_field(name="User ID:", value=user.id, inline=True)
    embed.add_field(name="Bot:", value=user.bot, inline=True)
    embed.add_field(name="Created at:", value=user.created_at.strftime("%B %d %Y, %T"), inline=True)
    embed.add_field(name="Joined at:", value=user.joined_at.strftime("%B %d %Y, %T"), inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clear", description="ลบข้อความในช่องแชท")
@app_commands.describe(amount="จำนวนข้อความที่จะลบ")
async def clear(interaction: discord.Interaction, amount: int = 5):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"ลบข้อความ {amount} ข้อความเรียบร้อยแล้ว", ephemeral=True)

@bot.tree.command(name="reminder", description="ตั้งการแจ้งเตือนเป็นระยะ")
@app_commands.describe(time="เวลาระหว่างแจ้งเตือน (นาที)", msg="ข้อความที่จะแจ้งเตือน")
async def reminder(interaction: discord.Interaction, time: int, msg: str):
    await interaction.response.send_message(f"การแจ้งเตือน `{msg}` จะถูกส่งทุกๆ {time} นาที")
    while True:
        await s(60 * time)
        await interaction.channel.send(f"{msg}, {interaction.user.mention}")

@bot.tree.command(name="activity", description="ดูข้อมูลกิจกรรมของ Ku")
async def activity(interaction: discord.Interaction):
    # สร้าง Embed
    embed = discord.Embed(
        title="กิจกรรม",
        description="ลองดูลิงก์ที่มีประโยชน์เหล่านี้เพื่อดูกิจกรรมที่เกี่ยวข้องกับ Ku",
        color=discord.Color.dark_teal()
    )
    
    # ตั้งค่า Author ของ Embed
    embed.set_author(
        name="KuBot",
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        icon_url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    # ตั้งค่า Thumbnail ของ Embed
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    # สร้าง View ที่มีปุ่มต่าง ๆ
    view = discord.ui.View()

    # เพิ่มปุ่ม 'ปฏิทินการศึกษา'
    view.add_item(
        discord.ui.Button(
            label="ปฏิทินการศึกษา", 
            style=discord.ButtonStyle.link, 
            url="https://ead.kps.ku.ac.th/2021/index.php?Itemid=162"
        )
    )

    # เพิ่มปุ่ม 'ประเมินการเรียนการสอน'
    view.add_item(
        discord.ui.Button(
            label="ประเมินการเรียนการสอน", 
            style=discord.ButtonStyle.link, 
            url="https://eassess.ku.ac.th/m/"
        )
    )

    # ส่ง Embed พร้อม View ที่มีปุ่มไปยังผู้ใช้
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="server", description="ดูข้อมูลเซิร์ฟเวอร์ปัจจุบัน")
async def server(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(color=discord.Color.dark_teal())
    embed.set_thumbnail(url=guild.icon)
    embed.set_author(name=guild.name, icon_url=guild.icon)
    embed.add_field(name="👑 Owner:", value=guild.owner.mention, inline=True)
    embed.add_field(name="💬 Channels:", value=len(guild.channels), inline=True)
    embed.add_field(name="👥 Members:", value=guild.member_count, inline=True)
    embed.add_field(name="📆 Created at:", value=guild.created_at.strftime("%B %d %Y, %T"), inline=True)
    embed.add_field(name="🆔 Server ID:", value=guild.id, inline=True)
    await interaction.response.send_message(embed=embed)
    
@bot.tree.command(name="help", description="ดูวิธีเริ่มต้นใช้งาน KuBot!")
async def help_command(interaction: discord.Interaction):
    # สร้าง Embed เพื่อนำเสนอข้อมูล
    embed = discord.Embed(
        title="ช่วยเหลือ",
        description="ลองดูลิงก์ที่มีประโยชน์เหล่านี้เพื่อเริ่มต้นใช้งาน KuBot!",
        color=discord.Color.dark_teal()
    )
    
    # ตั้งค่า Author และ Thumbnail ของ Embed
    embed.set_author(
        name="KuBot",
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        icon_url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    # สร้าง View สำหรับปุ่ม
    view = discord.ui.View()
    
    # ปุ่มเว็บไซต์
    button_website = discord.ui.Button(
        label="เว็บไซต์", 
        style=discord.ButtonStyle.link, 
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    # ปุ่มเชิญบอท
    button_invite = discord.ui.Button(
        label="เชิญ", 
        style=discord.ButtonStyle.link, 
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot"
    )
    
    # เพิ่มปุ่มลงใน View
    view.add_item(button_website)
    view.add_item(button_invite)

    # ส่ง Embed พร้อมกับปุ่ม
    await interaction.response.send_message(embed=embed, view=view)


bot.run(env("DISCORD_BOT_TOKEN"))

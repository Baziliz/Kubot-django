import os
import django
import json
import pytz

try:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {str(e)}")
    exit(1)

import discord
import asyncio
from discord import app_commands, ui
from discord.ext import commands, tasks
from accounts.models import DiscordProfile, StudentProfile, GPAX, StudentEducation, Schedule, GroupCourse, TeacherProfile, Event
import concurrent.futures
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async

timezone = pytz.timezone('Asia/Bangkok')  # กำหนด Timezone

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_schedule_notifications = {}

@tasks.loop(minutes=1)
async def schedule_notification_task():
    try:
        for user_id, settings in user_schedule_notifications.items():
            # Fetch course data
            course = await run_in_thread(lambda: GroupCourse.objects.get(id=settings['course_id']))
            current_time = datetime.now(timezone)

            # Check time condition based on user preference
            if settings['notification_time'] == '2_hours':
                notify_time = course.time_from - timedelta(hours=2)
            elif settings['notification_time'] == '1_day':
                notify_time = course.time_from - timedelta(days=1)

            # Send notification if the time is appropriate
            if current_time >= notify_time:
                user = await bot.fetch_user(int(user_id))
                if user:
                    await user.send(f"Reminder: Your class '{course.subject_name}' starts at {course.time_from}.")

    except Exception as e:
        print(f"Error in schedule notification task: {e}")

last_announcement_id = None  # Global variable to track the last sent announcement

@tasks.loop(minutes=1)
async def check_for_new_announcements():
    global last_announcement_id
    try:
        # Fetch the latest announcement
        latest_announcement = await sync_to_async(lambda: Event.objects.latest('id'))()

        # Check if it is a new announcement
        if last_announcement_id is None or latest_announcement.id > last_announcement_id:
            # Update the last_announcement_id
            last_announcement_id = latest_announcement.id

            # Notify subscribed users (as previously implemented)
            students = await sync_to_async(lambda: list(StudentProfile.objects.filter(group_courses__id=latest_announcement.course.id)))()

            for student in students:
                discord_profile = await sync_to_async(lambda: DiscordProfile.objects.get(user=student.user))()
                user = await bot.fetch_user(int(discord_profile.discord_id))

                if user:
                    embed = discord.Embed(
                        title=f"📢 New Announcement for {latest_announcement.title}",
                        description=latest_announcement.description,
                        color=discord.Color.dark_teal()
                    )
                    embed.add_field(name="Type", value=latest_announcement.event_type, inline=True)
                    embed.add_field(name="Date", value=f"{latest_announcement.start_date} to {latest_announcement.end_date}", inline=True)
                    embed.add_field(name="Time", value=f"{latest_announcement.start_time} - {latest_announcement.end_time}", inline=True)

                    await user.send(embed=embed)
    except Event.DoesNotExist:
        # No announcements exist yet
        pass
    except Exception as e:
        print(f"Error checking for new announcements: {e}")



@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('/help'))
    print(f"{bot.user.name} has connected to Discord!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    # Start tasks if they are not already running
    if not check_for_new_announcements.is_running():
        check_for_new_announcements.start()
    if not schedule_notification_task.is_running():
        schedule_notification_task.start()
        
        
@bot.tree.command(name="announcement", description="แสดงประกาศข้อมูลกิจกรรมหรือชดเชยการสอน")
async def announcement(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        # ดึงข้อมูลประกาศทั้งหมดจากฐานข้อมูล
        announcements = await run_in_thread(lambda: list(Event.objects.all()))
        
        if not announcements:
            await interaction.followup.send("ไม่มีประกาศในขณะนี้", ephemeral=True)
            return

        # สร้าง Embed สำหรับแสดงประกาศ
        embed = discord.Embed(title="📢 ประกาศกิจกรรมและชดเชยการสอน", color=discord.Color.dark_teal())
        
        for announcement in announcements:
            # เพิ่มประกาศใน Embed
            embed.add_field(
                name=announcement.title,
                value=(
                    f"ประเภท: {announcement.event_type}\n"
                    f"รายละเอียด: {announcement.description}\n"
                    f"วันที่: {announcement.start_date} ถึง {announcement.end_date}\n"
                    f"เวลา: {announcement.start_time} - {announcement.end_time}\n"
                ),
                inline=False
            )

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

@bot.tree.command(name="set_announcement", description="ตั้งการแจ้งเตือนและรับการอัปเดตเมื่อมีประกาศใหม่")
async def set_announcement(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Fetch the student's profile based on Discord ID
        discord_id = str(interaction.user.id)
        student_profile = await run_in_thread(lambda: StudentProfile.objects.get(user__discordprofile__discord_id=discord_id))
        
        # Fetch related group courses
        group_courses = await run_in_thread(lambda: list(GroupCourse.objects.filter(student_profile=student_profile)))
        
        if not group_courses:
            await interaction.followup.send("ไม่พบวิชาในระบบที่เกี่ยวข้องกับบัญชีนี้", ephemeral=True)
            return

        # Create options for course selection
        options = [
            discord.SelectOption(label=course.subject_name, description=course.subject_code, value=str(course.id))
            for course in group_courses
        ]

        # Create a dropdown menu
        select = ui.Select(placeholder="เลือกวิชาสำหรับการรับประกาศ", options=options)
        
        async def select_callback(interaction: discord.Interaction):
            selected_course_id = int(select.values[0])
            selected_course = await run_in_thread(lambda: GroupCourse.objects.get(id=selected_course_id))
            # Logic for subscribing the user to notifications for this course
            await interaction.response.send_message(
                f"คุณได้ตั้งค่าการแจ้งเตือนสำหรับวิชา {selected_course.subject_name} สำเร็จ", ephemeral=True
            )
        
        select.callback = select_callback

        # Button for closing notifications
        async def close_notification(interaction: discord.Interaction):
            # Logic for unsubscribing or stopping notifications can go here
            await interaction.response.send_message("การแจ้งเตือนถูกปิดสำหรับวิชาที่คุณเลือก", ephemeral=True)

        close_button = ui.Button(label="ปิดการแจ้งเตือน", style=discord.ButtonStyle.danger)
        close_button.callback = close_notification

        # Create the view and add elements
        view = ui.View()
        view.add_item(select)
        view.add_item(close_button)
        await interaction.followup.send("โปรดเลือกวิชาสำหรับการแจ้งเตือนหรือปิดการแจ้งเตือน:", view=view)

    except StudentProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบนิสิตที่เชื่อมกับบัญชีนี้", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

        
@bot.tree.command(name="my_courses", description="แสดงรายวิชาที่สอน (เฉพาะอาจารย์)")
async def my_courses(interaction: discord.Interaction):
    try:
        # ดึง TeacherProfile ของผู้ใช้ Discord
        teacher_profile = await run_in_thread(lambda: TeacherProfile.objects.get(user__discordprofile__discord_id=str(interaction.user.id)))
        
        # ดึงรายวิชาที่อาจารย์สอน
        courses = await run_in_thread(lambda: list(GroupCourse.objects.filter(teacher=teacher_profile)))

        if not courses:
            await interaction.response.send_message("คุณไม่มีรายวิชาที่สอน", ephemeral=True)
            return

        # สร้าง Embed สำหรับแสดงรายวิชา
        embed = discord.Embed(title="รายวิชาที่สอน", color=discord.Color.blue())
        for course in courses:
            embed.add_field(
                name=course.subject_name,
                value=f"รหัสวิชา: {course.subject_code}\nวัน: {course.day_w}\nเวลา: {course.time_from} - {course.time_to}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    except TeacherProfile.DoesNotExist:
        await interaction.response.send_message(
            "คำสั่งนี้สามารถใช้ได้เฉพาะอาจารย์เท่านั้น", ephemeral=True
        )

async def run_in_thread(func):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func)
        
@bot.tree.command(name="set_schedule", description="ตั้งค่าการแจ้งเตือนสำหรับวิชา")
async def set_notification(interaction: discord.Interaction):
    try:
        discord_id = str(interaction.user.id)
        student_profile = await run_in_thread(lambda: StudentProfile.objects.get(user__discordprofile__discord_id=discord_id))
        group_courses = await run_in_thread(lambda: list(GroupCourse.objects.filter(student_profile=student_profile)))

        course_options = [
            discord.SelectOption(
                label=course.subject_name,
                description=f"{course.subject_code}",
                value=str(course.id)
            )
            for course in group_courses
        ]
        notification_options = [
            discord.SelectOption(label="แจ้งเตือนล่วงหน้า 2 ชั่วโมง", value="2_hours"),
            discord.SelectOption(label="แจ้งเตือนล่วงหน้า 1 วัน", value="1_day")
        ]

        select_course = ui.Select(placeholder="เลือกวิชาสำหรับการแจ้งเตือน", options=course_options)
        select_notification = ui.Select(placeholder="เลือกประเภทการแจ้งเตือน", options=notification_options)

        async def course_callback(interaction: discord.Interaction):
            selected_course_id = int(select_course.values[0])
            selected_course = await run_in_thread(lambda: GroupCourse.objects.get(id=selected_course_id))
            await interaction.response.send_message(f"คุณเลือกวิชา {selected_course.subject_name}", ephemeral=True)

            # Store user preference
            user_schedule_notifications[discord_id] = {
                'course_id': selected_course_id,
                'notification_time': user_schedule_notifications[discord_id].get('notification_time', '2_hours')
            }

        async def notification_callback(interaction: discord.Interaction):
            selected_option = select_notification.values[0]
            await interaction.response.send_message(f"ตั้งค่าการแจ้งเตือน: {selected_option}", ephemeral=True)

            # Update user preference
            if discord_id in user_schedule_notifications:
                user_schedule_notifications[discord_id]['notification_time'] = selected_option

        async def close_notification(interaction: discord.Interaction):
            if discord_id in user_schedule_notifications:
                del user_schedule_notifications[discord_id]
            await interaction.response.send_message("การแจ้งเตือนถูกปิด", ephemeral=True)

        close_button = ui.Button(label="ปิดการแจ้งเตือน", style=discord.ButtonStyle.danger)
        close_button.callback = close_notification

        select_course.callback = course_callback
        select_notification.callback = notification_callback

        view = ui.View()
        view.add_item(select_course)
        view.add_item(select_notification)
        view.add_item(close_button)
        await interaction.response.send_message("โปรดเลือกวิชาและประเภทการแจ้งเตือน หรือปิดการแจ้งเตือน:", view=view)
    except Exception as e:
        await interaction.response.send_message(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

        
@bot.tree.command(name="schedule", description="แสดงตารางเรียนของนิสิตพร้อมรายละเอียดวิชา")
async def schedule(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        discord_profile = await run_in_thread(lambda: DiscordProfile.objects.get(discord_id=str(interaction.user.id)))
        student_profile = await run_in_thread(lambda: StudentProfile.objects.get(user=discord_profile.user))

        schedules = await run_in_thread(lambda: list(Schedule.objects.filter(student_profile=student_profile)))
        group_courses = await run_in_thread(lambda: list(GroupCourse.objects.filter(student_profile=student_profile)))

        if not schedules or not group_courses:
            await interaction.followup.send("ไม่มีข้อมูลตารางเรียนที่จะแสดง", ephemeral=True)
            return

        embed = discord.Embed(title="ตารางเรียน", color=discord.Color.dark_teal())

        for schedule in schedules:
            relevant_courses = [
                course for course in group_courses if str(schedule.academic_year) in course.period_date
            ]

            if relevant_courses:
                for course in relevant_courses:
                    embed.add_field(
                        name=f"{course.subject_name} ({course.subject_code})",
                        value=(
                            f"ผู้สอน: {course.teacher_name}\n"
                            f"เวลา: {course.time_from} - {course.time_to}\n"
                            f"วัน: {course.day_w.strip()}\n"
                            f"ห้อง: {course.room_name_th}"
                        ),
                        inline=False,
                    )
            else:
                embed.add_field(name="ไม่มีข้อมูลวิชา", value="ไม่พบข้อมูลกลุ่มวิชา", inline=False)

        await interaction.followup.send(embed=embed)

    except DiscordProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบนิสิตที่เชื่อมกับบัญชีนี้", ephemeral=True)
    except StudentProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบข้อมูลนิสิตในระบบ", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

async def run_in_thread(func):
    """Run blocking code in a separate thread to avoid blocking the event loop."""
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func)

@bot.tree.command(name="kuprofile", description="แสดงข้อมูลโปรไฟล์นิสิต")
async def kuprofile(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        discord_profile = await run_in_thread(lambda: DiscordProfile.objects.get(discord_id=str(interaction.user.id)))
        student_profile = await run_in_thread(lambda: StudentProfile.objects.get(user=discord_profile.user))

        embed = discord.Embed(
            title=f"โปรไฟล์ของ {student_profile.name_th}",
            color=discord.Color.dark_teal()
        )
        embed.add_field(name="รหัสนิสิต", value=student_profile.std_code, inline=True)
        embed.add_field(name="ชื่อ (TH)", value=student_profile.name_th, inline=True)
        embed.add_field(name="ชื่อ (EN)", value=student_profile.name_en, inline=True)
        embed.add_field(name="เพศ", value=student_profile.gender, inline=True)
        embed.add_field(name="ศาสนา", value=student_profile.religion, inline=True)
        embed.add_field(name="เบอร์โทร", value=student_profile.phone, inline=True)
        embed.add_field(name="Email", value=student_profile.email, inline=True)

        await interaction.followup.send(embed=embed)

    except DiscordProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบนิสิตที่เชื่อมกับบัญชีนี้", ephemeral=True)
    except StudentProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบข้อมูลนิสิตในระบบ", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

async def run_in_thread(func):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func)

@bot.tree.command(name="kugpax", description="แสดงหน่วยกิตกับเกรดเฉลี่ยของนิสิต")
async def kugpax(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        discord_profile = await run_in_thread(lambda: DiscordProfile.objects.get(discord_id=str(interaction.user.id)))
        student_profile = await run_in_thread(lambda: StudentProfile.objects.get(user=discord_profile.user))
        gpax_data = await run_in_thread(lambda: GPAX.objects.get(student_profile=student_profile))

        embed = discord.Embed(
            title=f"เกรดเฉลี่ยสะสมของ {student_profile.name_th}",
            color=discord.Color.dark_teal()
        )
        embed.add_field(name="หน่วยกิตสะสม", value=gpax_data.total_credit, inline=True)
        embed.add_field(name="เกรดเฉลี่ยสะสม", value=gpax_data.gpax, inline=True)

        await interaction.followup.send(embed=embed)

    except DiscordProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบนิสิตที่เชื่อมกับบัญชีนี้", ephemeral=True)
    except StudentProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบข้อมูลนิสิตในระบบ", ephemeral=True)
    except GPAX.DoesNotExist:
        await interaction.followup.send("ไม่พบข้อมูล GPAX ในระบบ", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

async def run_in_thread(func):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func)

@bot.tree.command(name="kueducation", description="แสดงข้อมูลการศึกษาของนิสิต")
async def kueducation(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        discord_profile = await run_in_thread(lambda: DiscordProfile.objects.get(discord_id=str(interaction.user.id)))
        student_profile = await run_in_thread(lambda: StudentProfile.objects.get(user=discord_profile.user))
        education_data = await run_in_thread(lambda: StudentEducation.objects.get(student_profile=student_profile))

        embed = discord.Embed(
            title=f"ข้อมูลการศึกษาของ {student_profile.name_th}",
            color=discord.Color.dark_teal()
        )
        embed.add_field(name="สถานภาพนิสิต", value=education_data.status, inline=True)
        embed.add_field(name="คณะ", value=education_data.faculty_name_th, inline=True)
        embed.add_field(name="สาขา", value=education_data.major_name_th, inline=True)
        embed.add_field(name="ชื่อปริญญา", value=education_data.degree_name, inline=True)

        await interaction.followup.send(embed=embed)

    except DiscordProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบนิสิตที่เชื่อมกับบัญชีนี้", ephemeral=True)
    except StudentProfile.DoesNotExist:
        await interaction.followup.send("ไม่พบข้อมูลนิสิตในระบบ", ephemeral=True)
    except StudentEducation.DoesNotExist:
        await interaction.followup.send("ไม่พบข้อมูลการศึกษาในระบบ", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)

async def run_in_thread(func):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, func)

@bot.tree.command(name="hello", description="ทักทาย Hello World!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello World!")

@bot.tree.command(name="invite", description="รับลิงก์เชิญบอท KuBot")
async def invite(interaction: discord.Interaction):
    embed = discord.Embed(
        color=discord.Color.dark_teal(),
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        description="KuBot เป็นวิธีที่สะดวกในการจัดการการเรียนของคุณ",
        title="เชิญฉันเข้าสู่เซิร์ฟเวอร์ของคุณ คลิกที่นี่!"
    )
    
    embed.set_author(
        name="KuBot",
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        icon_url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ping", description="ตรวจสอบ ping ของบอท")
async def ping(interaction: discord.Interaction):
    bot_latency = round(bot.latency * 1000, 2)

    embed = discord.Embed(
        title="🏓 Pong!",
        description="เช็คสถานะ Ping ของบอท",
        color=discord.Color.dark_teal()
    )
    
    embed.add_field(name="Latency:", value=f"`{bot_latency}` ms", inline=False)

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

user_reminder_tasks = {}

@bot.tree.command(name="activity", description="ดูข้อมูลกิจกรรมของ Ku")
async def activity(interaction: discord.Interaction):
    embed = discord.Embed(
        title="กิจกรรม",
        description="ลองดูลิงก์ที่มีประโยชน์เหล่านี้เพื่อดูกิจกรรมที่เกี่ยวข้องกับ Ku",
        color=discord.Color.dark_teal()
    )
    
    embed.set_author(
        name="KuBot",
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        icon_url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    view = discord.ui.View()

    view.add_item(
        discord.ui.Button(
            label="ปฏิทินการศึกษา", 
            style=discord.ButtonStyle.link, 
            url="https://ead.kps.ku.ac.th/2021/index.php?Itemid=162"
        )
    )

    view.add_item(
        discord.ui.Button(
            label="ประเมินการเรียนการสอน", 
            style=discord.ButtonStyle.link, 
            url="https://eassess.ku.ac.th/m/"
        )
    )

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
    embed = discord.Embed(
        title="คำสั่ง KuBot",
        description="รายชื่อคำสั่งทั้งหมดที่คุณสามารถใช้กับ KuBot",
        color=discord.Color.dark_teal()
    )

    embed.set_author(
        name="KuBot",
        url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot",
        icon_url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )
    embed.set_thumbnail(
        url="https://media.discordapp.net/attachments/881215262307786822/1235961567313657959/Your_paragraph_text.png?ex=66364668&is=6634f4e8&hm=d275a5557acfcf8fb9ce3926e8b798434a2cf231f0b248521db5dc836c1bd84a&=&format=webp&quality=lossless&width=640&height=640"
    )

    # เพิ่มข้อมูลคำสั่งทั้งหมดที่บอทมี
    commands = {
        "/my_courses": "แสดงรายวิชาที่สอน (เฉพาะอาจารย์)",
        "/schedule": "แสดงตารางเรียนของนิสิตพร้อมรายละเอียดวิชา",
        "/set_schedule": "ตั้งค่าการแจ้งเตือนสำหรับวิชา",
        "/announcement": "แสดงประกาศข้อมูลกิจกรรมหรือชดเชยการสอน",
        "/set_announcement": "ตั้งการแจ้งเตือนและรับการอัปเดตเมื่อมีประกาศใหม่",
        "/kuprofile": "แสดงข้อมูลโปรไฟล์นิสิต",
        "/kugpax": "แสดงหน่วยกิตกับเกรดเฉลี่ยของนิสิต",
        "/kueducation": "แสดงข้อมูลการศึกษาของนิสิต",
        "/invite": "รับลิงก์เชิญบอท KuBot",
        "/profile": "ดูโปรไฟล์ของผู้ใช้",
        "/clear": "ลบข้อความในช่องแชท",
        "/activity": "ดูข้อมูลกิจกรรมของ Ku",
        "/server": "ดูข้อมูลเซิร์ฟเวอร์ปัจจุบัน",
        "/help": "ดูวิธีเริ่มต้นใช้งาน KuBot!",
        "/tuition_due": "ตรวจสอบวันชำระเงินค่าธรรมเนียมการศึกษา",
        "/regdate": "ตรวจสอบวันลงทะเบียนการศึกษา",
        "/opendate": "ตรวจสอบวันเปิดภาคการศึกษา",
        "/late_reg": "วันลงทะเบียนสำหรับนิสิตที่ชำระเงินล่าช้าหรือลงทะเบียนไม่ทัน",
        "/withdraw_no_w": "ตรวจสอบวันขอถอนรายวิชาโดยไม่บันทึกอักษร W",
        "/withdraw_with_w": "ตรวจสอบวันขอถอนรายวิชา (บันทึกอักษร W)",
        "/exam_schedule": "ตรวจสอบวันสอบกลางภาคและปลายภาค",
        "/evaluation": "ตรวจสอบวันกรอกแบบประเมินการสอน",
        "/download_form": "ดาวน์โหลดเอกสารแบบฟอร์มคำร้องต่างๆที่ต้องการ",
        "/calendar": "แสดงเนื้อหาปฏิทินการศึกษาจาก PDF"
    }

    # เพิ่มคำสั่งทั้งหมดใน embed
    for command, description in commands.items():
        embed.add_field(name=command, value=description, inline=False)

    # ปุ่มลิงก์
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="เชิญ KuBot",
            style=discord.ButtonStyle.link,
            url="https://discord.com/oauth2/authorize?client_id=1295415714144059405&permissions=8&integration_type=0&scope=bot"
        )
    )

    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="tuition_due", description="ตรวจสอบวันชำระเงินค่าธรรมเนียมการศึกษา")
async def tuition_due(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 วันชำระเงินค่าธรรมเนียมการศึกษา",
        color=discord.Color.dark_teal()
    )
    
    # เพิ่มข้อมูลวันชำระเงินตามภาคการศึกษา
    embed.add_field(name="📘 ภาคต้น", value="จ. 3 - อา. 16 มิ.ย. 67", inline=True)
    embed.add_field(name="📙 ภาคปลาย", value="จ. 4 - อา. 17 พ.ย. 67", inline=False)
    embed.add_field(name="📗 ภาคฤดูร้อน ปี พ.ศ. 2568", value="จ. 7 - พฤ. 10 เม.ย. 68", inline=True)

    # ส่ง Embed ไปยังแชท
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="regdate", description="ตรวจสอบวันลงทะเบียนการศึกษา")
async def regdate(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 วันลงทะเบียนเรียนผ่านระบบสารสนเทศบริหารการศึกษา",
        description="กรุณาตรวจสอบวันลงทะเบียนของคุณตามภาคการศึกษาและรหัสนิสิต",
        color=discord.Color.dark_teal()
    )

    # ใช้ Emoji + ชื่อภาคการศึกษาให้เด่นชัด
    embed.add_field(
        name="📘 ภาคต้น",
        value=(
            "• **นิสิตรหัส 64 และน้อยกว่า**: อ. 18 มิ.ย. 67\n"
            "• **นิสิตรหัส 65**: พ. 19 มิ.ย. 67\n"
            "• **นิสิตรหัส 66**: พฤ. 20 มิ.ย. 67\n"
            "• **นิสิตรหัส 67**: ศ. 21 มิ.ย. 67"
        ),
        inline=False
    )

    embed.add_field(
        name="📙 ภาคปลาย",
        value=(
            "• **นิสิตรหัส 64 และน้อยกว่า**: อ. 19 พ.ย. 67\n"
            "• **นิสิตรหัส 65**: พฤ. 21 พ.ย. 67\n"
            "• **นิสิตรหัส 66**: ศ. 22 พ.ย. 67\n"
            "• **นิสิตรหัส 67**: พ. 20 พ.ย. 67"
        ),
        inline=False
    )

    embed.add_field(
        name="📗 ภาคฤดูร้อน",
        value=(
            "• **นิสิตรหัส 64 และน้อยกว่า**: พฤ. 17 เม.ย. 68\n"
            "• **นิสิตรหัส 65**: พฤ. 17 เม.ย. 68\n"
            "• **นิสิตรหัส 66**: ศ. 18 เม.ย. 68\n"
            "• **นิสิตรหัส 67**: ศ. 18 เม.ย. 68"
        ),
        inline=False
    )
    # สร้างปุ่มลิงก์ไปยังระบบสารสนเทศบริหารการศึกษา
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="เข้าสู่ระบบ my.ku.th", 
            style=discord.ButtonStyle.link, 
            url="https://my.ku.th/login"
        )
    )

    # ส่ง Embed ไปยังแชท
    await interaction.response.send_message(embed=embed, view=view)
    
@bot.tree.command(name="opendate", description="ตรวจสอบวันเปิดภาคการศึกษา")
async def opendate(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 วันเปิดภาคการศึกษา",
        description="ข้อมูลวันเปิดเรียนสำหรับแต่ละภาคการศึกษา",
        color=discord.Color.dark_teal()
    )

    # ข้อมูลวันเปิดภาคเรียน
    embed.add_field(
        name="📘 ภาคต้น",
        value="วันเปิดเรียน: **จ. 24 มิ.ย. 67**",
        inline=False
    )

    embed.add_field(
        name="📙 ภาคปลาย",
        value="วันเปิดเรียน: **จ. 25 พ.ย. 67**",
        inline=False
    )

    embed.add_field(
        name="📗 ภาคฤดูร้อน",
        value="วันเปิดเรียน: **จ. 21 เม.ย. 68**",
        inline=False
    )
    # ส่ง Embed พร้อมปุ่มไปยังแชท
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="late_reg", description="วันลงทะเบียนสำหรับนิสิตที่ชำระเงินล่าช้าหรือลงทะเบียนไม่ทัน")
async def late_reg(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 วันลงทะเบียนสำหรับนิสิตชำระเงินล่าช้าหรือลงทะเบียนไม่ทัน",
        description="ข้อมูลวันลงทะเบียนเพิ่มเติมสำหรับนิสิตที่ชำระเงินผ่านธนาคารล่าช้าหรือลงทะเบียนไม่ทันเวลา",
        color=discord.Color.dark_teal()
    )

    # ข้อมูลวันลงทะเบียนล่าช้าตามภาคเรียน
    embed.add_field(
        name="📘 ภาคต้น",
        value="วันลงทะเบียนเรียน: ** จ. 24  - ศ. 28 มิ.ย. 67**",
        inline=False
    )

    embed.add_field(
        name="📙 ภาคปลาย",
        value="วันลงทะเบียนเรียน: ** จ. 25 - ศ. 29 พ.ย. 67**",
        inline=False
    )

    embed.add_field(
        name="📗 ภาคฤดูร้อน",
        value="วันลงทะเบียนเรียน: **จ. 21 - ศ. 25 เม.ย. 68**",
        inline=False
    )

    # ปุ่มลิงก์ไปยังระบบสารสนเทศบริหารการศึกษา (my.ku.th)
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="เข้าสู่ระบบ my.ku.th", 
            style=discord.ButtonStyle.link, 
            url="https://my.ku.th/login"
        )
    )

    # ส่ง Embed พร้อมปุ่มไปยังแชท
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="withdraw_no_w", description="ตรวจสอบวันขอถอนรายวิชาโดยไม่บันทึกอักษร W")
async def withdraw_no_w(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 วันขอถอนรายวิชาโดยไม่บันทึกอักษร W",
        description="ข้อมูลวันขอถอนรายวิชาผ่านระบบสารสนเทศบริหารการศึกษา (my.ku.th)",
        color=discord.Color.dark_teal()
    )

    # ข้อมูลวันขอถอนรายวิชาโดยไม่บันทึก W
    embed.add_field(
        name="📘 ภาคต้น",
        value="วันขอถอน: **ส. 6 - อ. 23 ก.ค. 67**",
        inline=False
    )

    embed.add_field(
        name="📙 ภาคปลาย",
        value="วันขอถอน: **ส. 7 - อ. 24 ธ.ค. 67**",
        inline=False
    )

    embed.add_field(
        name="📗 ภาคฤดูร้อน",
        value="วันขอถอน: **ส. 3 - อ. 20 พ.ค. 68**",
        inline=False
    )

    # ปุ่มลิงก์ไปยังระบบสารสนเทศบริหารการศึกษา
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="เข้าสู่ระบบ my.ku.th", 
            style=discord.ButtonStyle.link, 
            url="https://my.ku.th/login"
        )
    )
    # ส่ง Embed พร้อมปุ่มไปยังแชท
    await interaction.response.send_message(embed=embed, view=view)
    
@bot.tree.command(name="withdraw_with_w", description="ตรวจสอบวันขอถอนรายวิชา (บันทึกอักษร W)")
async def withdraw_with_w(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 วันขอถอนรายวิชา (บันทึกอักษร W)",
        description="ข้อมูลวันขอถอนรายวิชาผ่านระบบสารสนเทศบริหารการศึกษา (my.ku.th)",
        color=discord.Color.dark_teal()
    )

    # ข้อมูลวันขอถอนรายวิชา (บันทึกอักษร W)
    embed.add_field(
        name="📘 ภาคต้น",
        value="ขอถอนพร้อม W: **พ. 24 ก.ค. - พฤ. 22 ส.ค. 67**",
        inline=False
    )

    embed.add_field(
        name="📙 ภาคปลาย",
        value="ขอถอนพร้อม W: **พ. 25 ธ.ค. 67 - พฤ. 23 ม.ค. 68**",
        inline=False
    )

    embed.add_field(
        name="📗 ภาคฤดูร้อน",
        value="วันขอถอนพร้อม W: **-**",
        inline=False
    )

    # ปุ่มลิงก์ไปยังระบบสารสนเทศบริหารการศึกษา
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="เข้าสู่ระบบ my.ku.th", 
            style=discord.ButtonStyle.link, 
            url="https://my.ku.th/login"
        )
    )

    # ส่ง Embed พร้อมปุ่มไปยังแชท
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="exam_schedule", description="ตรวจสอบวันสอบกลางภาคและปลายภาค")
async def exam_schedule(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📅 วันสอบกลางภาคและปลายภาค",
        description="ตรวจสอบวันสอบสำหรับภาคต้นภาคปลาย",
        color=discord.Color.dark_teal()
    )

    # ข้อมูลสอบภาคต้น
    embed.add_field(
        name="📘 ภาคต้น",
        value=(
            "• **สอบกลางภาค**: ส. 10 - อา. 18 ส.ค. 67\n"
            "• **สอบปลายภาค**: ส. 11 - อา. 19 ม.ค. 68"
        ),
        inline=False
    )

    # ข้อมูลสอบภาคปลาย
    embed.add_field(
        name="📙 ภาคปลาย",
        value=(
            "• **สอบกลางภาค**:  จ. 21 ต.ค. - ศ. 1 พ.ย. 67\n"
            "• **สอบปลายภาค**:  จ. 17 - ศ. 28 มี.ค 68"
        ),
        inline=False
    )

    # ข้อมูลสอบภาคฤดูร้อน
    embed.add_field(
        name="📗 ภาคฤดูร้อน",
        value=(
            "• **สอบกลางภาค**: -\n"
            "• **สอบปลายภาค**: ส. 31 พ.ค - จ. 2 มิ.ย. 68"
        ),
        inline=False
    )

    # ปุ่มลิงก์ไปยังระบบสารสนเทศบริหารการศึกษา
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="เข้าสู่ระบบ my.ku.th", 
            style=discord.ButtonStyle.link, 
            url="https://my.ku.th/login"
        )
    )

    # ส่ง Embed พร้อมปุ่มไปยังแชท
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="evaluation", description="ตรวจสอบวันกรอกแบบประเมินการสอน")
async def evaluation(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 นิสิตกรอกแบบประเมินการสอน (ภาคต้นและภาคปลาย)",
        description="กรอกแบบประเมินการสอนตามช่วงเวลาที่กำหนดผ่านระบบประเมินการเรียนการสอน",
        color=discord.Color.dark_teal()
    )

    # ข้อมูลการกรอกแบบประเมินภาคต้น
    embed.add_field(
        name="📘 ภาคต้น",
        value=(
            "• **ครั้งที่ 1**: จ. 5 - ศ. 9 ส.ค. 67\n"
            "• **ครั้งที่ 2**: จ. 14 - ศ. 18 ต.ค. 67"
        ),
        inline=False
    )

    # ข้อมูลการกรอกแบบประเมินภาคปลาย
    embed.add_field(
        name="📙 ภาคปลาย",
        value=(
            "• **ครั้งที่ 1**: จ. 6 - ศ. 10 ม.ค. 68\n"
            "• **ครั้งที่ 2**:  จ. 10 - ศ. 14 มี.ค. 68"
        ),
        inline=False
    )

    # ปุ่มลิงก์ไปยังระบบสารสนเทศบริหารการศึกษา
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="ประเมินการเรียนการสอน", 
            style=discord.ButtonStyle.link, 
            url="https://eassess.ku.ac.th/m/"
        )
    )

    # ส่ง Embed พร้อมปุ่มไปยังแชท
    await interaction.response.send_message(embed=embed, view=view)

# Dictionary to store form names and file paths
form_files = {
    "ใบลงทะเบียน KU3 Add-Drop Form": "D:/Github/Kubot-django/myproject/frontend/public/KU3 Add-Drop form.pdf",
    "ใบลงทะเบียน KU1 Registration Form": "D:/Github/Kubot-django/myproject/frontend/public/KU1 Registration Form.pdf",
    "คำร้องขอลงทะเบียนเรียน Request for Resignation": "D:/Github/Kubot-django/myproject/frontend/public/Request for Resignation.pdf",
    "คำร้องทั่วไป General Request": "D:/Github/Kubot-django/myproject/frontend/public/General Request.pdf",
    "ใบลาพักการศึกษา Request fpr Leave of Absence Request": "D:/Github/Kubot-django/myproject/frontend/public/Request fpr Leave of Absence Request.pdf",
    "ใบลาออก Resignation Form": "D:/Github/Kubot-django/myproject/frontend/public/Resignation Form.pdf"
}

@bot.tree.command(name="download_form", description="ดาวน์โหลดเอกสารแบบฟอร์มคำร้องต่างๆที่ต้องการ")
async def download_form(interaction: discord.Interaction):
    # Create the main embed message
    embed = discord.Embed(
        title="ดาวน์โหลดแบบฟอร์มคำร้องต่างๆ",
        description="กดที่ปุ่มเพื่อดาวน์โหลดเอกสารแบบฟอร์มคำร้องต่างๆ",
        color=discord.Color.dark_teal()
    )
    view = discord.ui.View()

    # Arrange buttons in rows
    row_index = 0
    for i, (form_name, file_path) in enumerate(form_files.items()):
        # Define a callback function for each button that captures the specific file_path
        async def send_file_callback(interaction: discord.Interaction, path=file_path, name=form_name):
            with open(path, "rb") as file:
                await interaction.response.send_message(file=discord.File(file, filename=name + ".pdf"), ephemeral=True)

        # Create a button and set its callback to the send_file_callback function
        button = discord.ui.Button(label=form_name, style=discord.ButtonStyle.primary, row=row_index)
        button.callback = send_file_callback  # Set callback directly without lambda
        view.add_item(button)

        # Update row index for the next button to organize them in rows of 3
        if (i + 1) % 3 == 0:
            row_index += 1

    await interaction.response.send_message(embed=embed, view=view)

# โหลดข้อมูลจากไฟล์ JSON เมื่อบอทเริ่มทำงาน
with open("D:\Github\Kubot-django\myproject\pdf.json", "r", encoding="utf-8") as json_file:
    calendar_data = json.load(json_file)

@bot.tree.command(name="calendar", description="แสดงเนื้อหาปฏิทินการศึกษาจาก PDF")
@app_commands.describe(page_number="หมายเลขหน้าที่ต้องการดู")
async def calendar(interaction: discord.Interaction, page_number: int):
    try:
        # ตรวจสอบว่าหมายเลขหน้าถูกต้อง
        total_pages = calendar_data["document"]["total_pages"]
        if page_number < 1 or page_number > total_pages:
            await interaction.response.send_message(
                f"กรุณาระบุหมายเลขหน้าระหว่าง 1 และ {total_pages}", ephemeral=True
            )
            return

        # ดึงข้อมูลเนื้อหาของหน้าที่ผู้ใช้ระบุ
        page_content = next(
            (page["content"] for page in calendar_data["document"]["pages"] if page["page_number"] == page_number),
            None
        )

        if page_content:
            # ปรับรูปแบบข้อความให้ดูอ่านง่ายขึ้น
            formatted_content = page_content.replace("•", "\n•").replace(":", ":\n")

            # ส่งข้อความเนื้อหาของหน้าไปยัง Discord
            embed = discord.Embed(
                title=f"{calendar_data['document']['title']} - Page {page_number}",
                description=formatted_content,
                color=discord.Color.dark_teal()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("ไม่พบเนื้อหาของหน้าที่ระบุ", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"เกิดข้อผิดพลาด: {str(e)}", ephemeral=True)
        
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
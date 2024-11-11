from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .manager import UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

# Create your models here.


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'), 
    ]
    
    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student') 

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }



class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    std_id = models.CharField(max_length=20, unique=True)
    std_code = models.CharField(max_length=20, unique=True)
    name_th = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255)
    birth_date = models.DateField()
    gender = models.CharField(max_length=20)
    religion = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    ku_email = models.EmailField(blank=True, null=True)  # เพิ่มฟิลด์นี้

    def __str__(self):
        return f"{self.std_code} - {self.name_en}"

class TeacherProfile(models.Model):
    """โปรไฟล์ของอาจารย์"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    full_name = models.CharField(max_length=255)  # ชื่อที่ต้องตรงกับ teacher_name ใน GroupCourse
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} - {self.department}"
    
class Schedule(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='schedules')
    academic_year = models.IntegerField()
    semester = models.IntegerField()

    def __str__(self):
        return f"Schedule for {self.student_profile.std_id} - Year: {self.academic_year}, Semester: {self.semester}"


class Grade(models.Model):
    student_profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='grades'
    )
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=10) 
    subject_code = models.CharField(max_length=20)
    subject_name_th = models.CharField(max_length=255)
    subject_name_en = models.CharField(max_length=255, blank=True, null=True)
    credit = models.FloatField()
    grade = models.CharField(max_length=2)
    gpa = models.FloatField(null=True, blank=True)
    total_credits = models.FloatField(null=True, blank=True) 

    def __str__(self):
        return f"Grade for {self.student_profile.std_code} - {self.subject_name_th}: {self.grade}"


class GroupCourse(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='group_courses')
    period_date = models.CharField(max_length=50)
    subject_code = models.CharField(max_length=20)
    subject_name = models.CharField(max_length=255)
    teacher_name = models.CharField(max_length=255)
    teacher = models.ForeignKey('TeacherProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='group_courses')
    time_from = models.CharField(max_length=10)  
    time_to = models.CharField(max_length=10)  
    day_w = models.CharField(max_length=20)    
    room_name_th = models.CharField(max_length=255)  

    def save(self, *args, **kwargs):
        # เชื่อมโยง TeacherProfile โดยการค้นหาจาก teacher_name
        if self.teacher_name:
            try:
                # ค้นหา TeacherProfile ที่มี full_name ตรงกับ teacher_name
                teacher_profile = TeacherProfile.objects.get(full_name=self.teacher_name)
                self.teacher = teacher_profile
            except ObjectDoesNotExist:
                # ตั้งค่าเป็น None หากไม่พบ TeacherProfile ที่ตรงกัน
                self.teacher = None  

        super().save(*args, **kwargs)  # บันทึก instance ปัจจุบัน


class StudentEducation(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='educations')
    faculty_name_th = models.CharField(max_length=255)
    major_name_th = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    degree_name = models.CharField(max_length=255)

    def __str__(self):
        return f"Education for {self.student_profile.std_id} - {self.faculty_name_th}, {self.major_name_th}"

class Announcement(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='announcements')
    announce_message_th = models.TextField()
    teacher_name = models.CharField(max_length=255)

    def __str__(self):
        return f"Announcement for {self.student_profile.std_id} - {self.announce_message_th[:30]}"


class GPAX(models.Model):
    student_profile = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='gpax')
    gpax = models.FloatField()
    total_credit = models.IntegerField()

    def __str__(self):
        return f"GPAX for {self.student_profile.std_id}: {self.gpax}"

class OneTimePassword(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(default=now)  # บันทึกเวลาที่สร้าง OTP

    def __str__(self):
        return f"{self.user.first_name} - {self.code}"
    
class DiscordProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True
    )
    discord_id = models.CharField(max_length=255, unique=True)
    discord_username = models.CharField(max_length=255)
    discord_discriminator = models.CharField(max_length=4)
    avatar_url = models.URLField()
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255, blank=True, null=True)
    expires_in = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.discord_username}#{self.discord_discriminator}"
    
class TeachingSchedule(models.Model):
    # ตารางสอนของอาจารย์ที่เชื่อมกับ GroupCourse โดยตรง
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='schedules'
    )
    group_course = models.ForeignKey(
        GroupCourse, on_delete=models.CASCADE, related_name='teaching_schedules', null=True, blank=True
    )
    subject_code = models.CharField(max_length=20)  # เพิ่ม subject_code เพื่อใช้จับคู่ GroupCourse
    start_date = models.DateField()
    end_date = models.DateField()
    days_of_week = models.CharField(max_length=50, default="Monday")  # เช่น "Monday, Wednesday"
    start_time = models.TimeField(default="00:00")
    end_time = models.TimeField(default="00:00")

    def save(self, *args, **kwargs):
        # เชื่อมโยง GroupCourse ที่ตรงกับ subject_code และ teacher
        if not self.group_course:
            try:
                # หา GroupCourse ที่ตรงกันตาม subject_code และ teacher
                teacher_profile = self.teacher.teacher_profile
                group_course = GroupCourse.objects.get(
                    subject_code=self.subject_code,
                    teacher=teacher_profile
                )
                self.group_course = group_course
            except ObjectDoesNotExist:
                raise ValueError("ไม่พบ GroupCourse ที่ตรงกับ subject_code และ teacher")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.group_course.subject_name} - {self.teacher.get_full_name()}"

class Event(models.Model):
    EVENT_TYPES = [
        ('makeup_class', 'Makeup Class'),
        ('assignment', 'Assignment'),
        ('announcement', 'Announcement'),
    ]

    course = models.ForeignKey(GroupCourse, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    start_time = models.TimeField(default=timezone.now)
    end_time = models.TimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - {self.get_event_type_display()} ({self.course.subject_name})"
    
class TeachingAnnouncement(models.Model):
    # ประกาศจากอาจารย์ที่เกี่ยวกับคอร์สเรียน
    schedule = models.ForeignKey(
        TeachingSchedule, on_delete=models.CASCADE, related_name='teaching_announcements'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    due_date = models.DateField(null=True, blank=True)  # วันที่ประกาศหมดอายุ
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - Announcement"

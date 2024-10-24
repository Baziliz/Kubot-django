from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .manager import UserManager
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.utils.timezone import now




# Create your models here.


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True, verbose_name=_("Email Address"))
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    myku_username = models.CharField(max_length=255, blank=True, null=True)
    myku_password = models.CharField(max_length=255, blank=True, null=True)
    myku_student_data = models.JSONField(blank=True, null=True)

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
    name_th = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255)
    birth_date = models.DateField()
    gender = models.CharField(max_length=20)
    religion = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return f"{self.std_id} - {self.name_th}"


class Schedule(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='schedules')
    academic_year = models.IntegerField()
    semester = models.IntegerField()

    def __str__(self):
        return f"Schedule for {self.student_profile.std_id} - Year: {self.academic_year}, Semester: {self.semester}"


class Grade(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    academic_year = models.CharField(max_length=20)
    subject_code = models.CharField(max_length=20)
    subject_name = models.CharField(max_length=255)
    credit = models.FloatField()
    grade = models.CharField(max_length=2)

    def __str__(self):
        return f"Grade for {self.student_profile.std_id} - {self.subject_name}: {self.grade}"


class GroupCourse(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='group_courses')
    period_date = models.CharField(max_length=50)
    subject_code = models.CharField(max_length=20)
    subject_name = models.CharField(max_length=255)
    teacher_name = models.CharField(max_length=255)

    def __str__(self):
        return f"GroupCourse for {self.student_profile.std_id} - {self.subject_name}"


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

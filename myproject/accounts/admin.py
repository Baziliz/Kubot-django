# admin.py

from django.contrib import admin
from .models import TeacherProfile, GroupCourse, User

class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'phone', 'user')
    search_fields = ('full_name', 'department')

class GroupCourseAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'subject_code', 'teacher_name', 'teacher', 'period_date')
    search_fields = ('subject_name', 'subject_code', 'teacher_name')
    list_filter = ('period_date', 'day_w')

    def save_model(self, request, obj, form, change):
        """เชื่อมโยง TeacherProfile กับ GroupCourse ถ้าพบชื่อที่ตรงกัน"""
        if obj.teacher_name:
            try:
                teacher = TeacherProfile.objects.get(full_name=obj.teacher_name)
                obj.teacher = teacher
            except TeacherProfile.DoesNotExist:
                obj.teacher = None  # ถ้าไม่พบอาจารย์ ปล่อยว่างไว้
        super().save_model(request, obj, form, change)

admin.site.register(User)  # ให้ Admin จัดการผู้ใช้ทั้งหมดได้
admin.site.register(TeacherProfile, TeacherProfileAdmin)
admin.site.register(GroupCourse, GroupCourseAdmin)

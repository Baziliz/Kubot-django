# manager.py

from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(_("You must provide a valid email address."))
        
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError(_("You must provide an email address."))
        if not first_name:
            raise ValueError(_("You must provide a first name."))
        if not last_name:
            raise ValueError(_("You must provide a last name."))
        
        extra_fields.setdefault('role', 'student') 
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_teacher(self, email, first_name, last_name, password=None, **extra_fields):
        """สร้างบัญชีอาจารย์พร้อม TeacherProfile"""
        extra_fields.setdefault('is_staff', True) 
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'teacher')  

        user = self.create_user(email, first_name, last_name, password, **extra_fields)
        
        from .models import TeacherProfile
        TeacherProfile.objects.create(user=user, full_name=f"{first_name} {last_name}")

        return user
    
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'admin')  # กำหนด role เป็น admin

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        
        return self.create_user(email, first_name, last_name, password, **extra_fields)

from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import smart_str, smart_bytes
from django.urls import reverse
from .utils import send_normal_email
from rest_framework_simplejwt.tokens import RefreshToken, Token
from pymyku import Client, requests
from datetime import datetime

import json
import pymyku
import requests as req_lib  # ใช้สำหรับจัดการ exceptions


class DiscordConnectSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=255, required=True)

    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("Authorization code is required")
        return value


class LoginWithMykuSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            # สร้าง Client และล็อกอิน
            client = Client(username=username, password=password)
            client.login()

            # ดึงข้อมูลนักศึกษาหลักทั้งหมด
            student_data = client.fetch_student_personal()
            schedule_data = client.fetch_schedule()
            announce_data = client.fetch_announce()
            grades_data = client.fetch_grades()
            group_course_data = client.fetch_group_course()
            student_education_data = client.fetch_student_education()
            gpax_data = client.fetch_gpax()

            # การตรวจสอบรูปแบบของข้อมูล เช่น birthDate
            birth_date_str = student_data.get('results', {}).get('stdPersonalModel', {}).get('birthDate', None)
            if birth_date_str:
                try:
                    # แปลงจาก ISO format เป็น YYYY-MM-DD
                    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    student_data['results']['stdPersonalModel']['birthDate'] = birth_date.strftime("%Y-%m-%d")
                except ValueError:
                    raise serializers.ValidationError("Invalid date format. Expected 'YYYY-MM-DD' or similar.")

            # เก็บข้อมูลทั้งหมดใน attrs เพื่อใช้ใน View
            attrs['student_data'] = student_data
            attrs['schedule_data'] = schedule_data
            attrs['announce_data'] = announce_data
            attrs['grades_data'] = grades_data
            attrs['group_course_data'] = group_course_data
            attrs['student_education_data'] = student_education_data
            attrs['gpax_data'] = gpax_data

        except Exception as e:
            raise serializers.ValidationError(f"Failed to log in to MyKU: {str(e)}")

        return attrs

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=68, min_length=6, write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']
        
    def validate(self, attrs):
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')
        if password != password2:
            raise serializers.ValidationError('Passwords do not match')
        
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email = validated_data['email'],
            first_name = validated_data.get('first_name'),
            last_name = validated_data.get('last_name'),
            password = validated_data.get('password')

        )
        return user
    
class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    
class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class LoginUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=6)
    password = serializers.CharField(max_length=68, write_only=True)
    full_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'access_token', 'refresh_token']
        
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request = self.context.get('request')

        # ตรวจสอบข้อมูลล็อกอิน
        user = authenticate(request, email=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials, try again.")
        if not user.is_verified:
            raise AuthenticationFailed("Email is not verified.")

        # ดึง JWT tokens จาก user
        user_tokens = user.tokens()

        # คืนค่าข้อมูล
        return {
            'email': user.email,
            'full_name': user.get_full_name,
            'access_token': str(user_tokens.get('access')),
            'refresh_token': str(user_tokens.get('refresh'))
        }

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ['email']
        
    def validate(self, attrs):
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            request = self.context.get('request')
            site_domain = 'localhost:5173'
            relative_link = f'/password-reset-confirm/{uidb64}/{token}/'
            abslink = f"http://{site_domain}{relative_link}"
            email_body = f"Hi use the link below to reset your password \n{abslink}"
            data = {
                'email_body': email_body,
                'email-subject':"Reset your password",
                'to_email': user.email,
            }
            send_normal_email(data)
        return super().validate(attrs)
    
class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    
    class Meta:
        fields = ['password', 'confirm_password', 'uidb64', 'token']
        
    def validate(self, attrs):
        try:
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')
            password = attrs.get('password')
            confirm_password = attrs.get('confirm_password')
            
            # Debug: Print the received values
            print(f"Token: {token}, UIDB64: {uidb64}")

            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            # Debug: Print the user information
            print(f"User ID: {user_id}, User: {user}")

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid or has expired', 401)

            if password != confirm_password:
                raise AuthenticationFailed('Password and confirm password do not match', 401)

            user.set_password(password)
            user.save()
            return user
        except User.DoesNotExist:
            raise AuthenticationFailed('The user does not exist', 401)
        except Exception as e:
            print(f"Exception: {e}")
            raise AuthenticationFailed('The reset link is invalid or has expired', 401)
        
class LogoutUserSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
    
    default_error_messages = {
        'bad_token': ('Token is expired or invalid'),
    }
    
    def validate(self, attrs):
        self.token = attrs.get('refresh_token')
        return attrs
    
    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            return self.fail('bad_token')
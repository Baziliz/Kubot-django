from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from .serializers import UserRegisterSerializer, LoginUserSerializer, SetNewPasswordSerializer, PasswordResetRequestSerializer, LogoutUserSerializer, EmailSerializer, VerifyOtpSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .utils import send_code_to_user
from .models import OneTimePassword, User, StudentProfile, Schedule, Grade, GroupCourse, StudentEducation, GPAX, Announcement, DiscordProfile
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from pymyku import Client
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
import logging
logger = logging.getLogger(__name__)

from .serializers import LoginWithMykuSerializer, DiscordConnectSerializer

User = get_user_model()
import requests
import environ
env = environ.Env()
environ.Env.read_env()

class StudentDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # ดึงข้อมูลโปรไฟล์นิสิตที่เชื่อมต่อกับผู้ใช้ปัจจุบัน
            student_profile = StudentProfile.objects.get(user=request.user)

            data = {
                "std_id": student_profile.std_id,
                "name_th": student_profile.name_th,
                "name_en": student_profile.name_en,
                "birth_date": student_profile.birth_date,
                "gender": student_profile.gender,
                "email": student_profile.email,
            }

            return Response(data, status=200)
        except StudentProfile.DoesNotExist:
            return Response({"error": "Student profile not found."}, status=404)

class DiscordConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info("DiscordConnectView ถูกเรียก")
        user = request.user
        code = request.data.get('code')

        if not code:
            logger.error("ไม่มี authorization code ถูกส่งมา")
            return Response({'error': 'No authorization code provided'}, status=400)

        # ตัวอย่างการแลกเปลี่ยน token
        token_response = requests.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if token_response.status_code != 200:
            logger.error(f"Failed to retrieve access token: {token_response.text}")
            return Response({'error': 'Failed to retrieve access token'}, status=400)

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        user_response = requests.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            logger.error(f"Failed to retrieve user info: {user_response.text}")
            return Response({'error': 'Failed to retrieve user info'}, status=400)

        discord_user_data = user_response.json()
        logger.info(f"ดึงข้อมูลผู้ใช้จาก Discord สำเร็จ: {discord_user_data}")

        DiscordProfile.objects.update_or_create(
            discord_id=discord_user_data['id'],
            defaults={
                'user': user,
                'discord_username': discord_user_data['username'],
                'discord_discriminator': discord_user_data['discriminator'],
                'avatar_url': f"https://cdn.discordapp.com/avatars/{discord_user_data['id']}/{discord_user_data['avatar']}.png",
                'access_token': access_token,
            }
        )

        logger.info(f"โปรไฟล์ Discord ของ {user.email} ถูกบันทึกสำเร็จ")
        return Response({'message': 'Successfully connected to Discord'}, status=200)

class DiscordCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        jwt_token = request.query_params.get('state')  # ดึง JWT token จาก state

        if not code or not jwt_token:
            return Response({'error': 'Authorization code or JWT token missing'}, status=400)

        # ตรวจสอบ JWT token เพื่อดึงผู้ใช้ที่ล็อกอิน
        user = self.get_authenticated_user(jwt_token)

        # แลกเปลี่ยน code เป็น access token
        token_response = requests.post(
            'https://discord.com/api/oauth2/token',
            data={
                'client_id': settings.DISCORD_CLIENT_ID,
                'client_secret': settings.DISCORD_CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': 'http://localhost:8000/api/v1/auth/discord/callback/',
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if token_response.status_code != 200:
            return Response({'error': 'Failed to retrieve access token'}, status=400)

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        # ดึงข้อมูลผู้ใช้จาก Discord API
        user_response = requests.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if user_response.status_code != 200:
            return Response({'error': 'Failed to retrieve user info'}, status=400)

        discord_user_data = user_response.json()

        # บันทึกโปรไฟล์ Discord
        DiscordProfile.objects.update_or_create(
            discord_id=discord_user_data['id'],
            defaults={
                'user': user,  # เชื่อมกับผู้ใช้ที่ได้รับจาก JWT
                'discord_username': discord_user_data['username'],
                'discord_discriminator': discord_user_data['discriminator'],
                'avatar_url': f"https://cdn.discordapp.com/avatars/{discord_user_data['id']}/{discord_user_data['avatar']}.png",
                'access_token': access_token,
            }
        )

        return redirect('http://localhost:5173/profile?discord_connected=true')

    def get_authenticated_user(self, token):
        # ตรวจสอบ JWT token เพื่อดึงผู้ใช้ที่ล็อกอิน
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)

        if not user:
            raise AuthenticationFailed("User not authenticated")

        return user

class DiscordProfileView(APIView):
    permission_classes = [IsAuthenticated]  # ต้องล็อกอินก่อนเข้าถึง

    def get(self, request):
        logger.info(f"Request user: {request.user}")
        if not request.user.is_authenticated:
            return Response({"error": "User is not authenticated"}, status=401)

        try:
            profile = DiscordProfile.objects.get(user=request.user)
            data = {
                "discord_username": profile.discord_username,
                "discord_discriminator": profile.discord_discriminator,
                "avatar_url": profile.avatar_url,
            }
            return Response(data, status=200)
        except DiscordProfile.DoesNotExist:
            return Response({"error": "ไม่พบบัญชี Discord ที่เชื่อมต่อ"}, status=404)

class MykuLoginView(GenericAPIView):
    serializer_class = LoginWithMykuSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                # รับข้อมูลจาก serializer ที่ validate แล้ว
                student_data = serializer.validated_data['student_data']
                schedule_data = serializer.validated_data['schedule_data']
                announce_data = serializer.validated_data['announce_data']
                grades_data = serializer.validated_data['grades_data']
                group_course_data = serializer.validated_data['group_course_data']
                student_education_data = serializer.validated_data['student_education_data']
                gpax_data = serializer.validated_data['gpax_data']

                # ดึงหรือสร้าง StudentProfile จาก User
                student_results = student_data['results']['stdPersonalModel']
                student_profile, created = StudentProfile.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'std_id': student_results['stdId'],
                        'name_th': student_results['nameTh'],
                        'name_en': student_results['nameEn'],
                        'birth_date': student_results['birthDate'],
                        'gender': student_results['genderTh'],
                        'religion': student_results['religionTh'],
                        'phone': student_results['phone'],
                        'email': student_results['email'],
                    }
                )

                # บันทึกข้อมูลตารางเรียน (Schedule)
                if schedule_data and 'results' in schedule_data:
                    for schedule in schedule_data['results']:
                        Schedule.objects.update_or_create(
                            student_profile=student_profile,
                            academic_year=schedule['academicYr'],
                            semester=schedule['semester'],
                        )

                # บันทึกข้อมูลประกาศ (Announcement)
                if announce_data and 'results' in announce_data:
                    for announcement in announce_data['results']:
                        # สามารถบันทึกข้อมูลประกาศเพิ่มเติมได้ หากต้องการ
                        pass

                # บันทึกข้อมูลเกรด (Grade)
                if grades_data and 'results' in grades_data:
                    for semester in grades_data['results']:
                        for course in semester['grade']:
                            Grade.objects.update_or_create(
                                student_profile=student_profile,
                                academic_year=semester['academicYear'],
                                subject_code=course['subject_code'],
                                defaults={
                                    'subject_name': course['subject_name_th'],
                                    'credit': course['credit'],
                                    'grade': course['grade'],
                                }
                            )

                # บันทึกข้อมูลกลุ่มวิชา (GroupCourse)
                if group_course_data and 'results' in group_course_data:
                    for group in group_course_data['results']:
                        for course in group['course']:
                            GroupCourse.objects.update_or_create(
                                student_profile=student_profile,
                                subject_code=course['subject_code'],
                                defaults={
                                    'period_date': group['peroid_date'],
                                    'subject_name': course['subject_name_th'],
                                    'teacher_name': course['teacher_name'],
                                }
                            )

                # บันทึกข้อมูลการศึกษา (StudentEducation)
                if student_education_data and 'results' in student_education_data:
                    for edu in student_education_data['results']['education']:
                        StudentEducation.objects.update_or_create(
                            student_profile=student_profile,
                            defaults={
                                'faculty_name_th': edu['facultyNameTh'],
                                'major_name_th': edu['majorNameTh'],
                                'status': edu['statusNameTh'],
                                'degree_name': edu['degreeNameTh'],
                            }
                        )

                # บันทึกข้อมูล GPAX
                if gpax_data and 'results' in gpax_data:
                    for gpax in gpax_data['results']:
                        GPAX.objects.update_or_create(
                            student_profile=student_profile,
                            defaults={
                                'gpax': gpax['gpax'],
                                'total_credit': gpax['total_credit'],
                            }
                        )

                return Response({
                    'student_data': student_data,
                    'message': 'Successfully linked MyKU and saved all data.'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MykuDataView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # ดึงข้อมูลผู้ใช้ที่ล็อกอินอยู่
            user = request.user

            # สมมติว่า User model เก็บ username และ password ที่ใช้กับ MyKU
            myku_username = user.myku_username
            myku_password = user.myku_password

            # ตรวจสอบข้อมูล MyKU ว่ามีครบถ้วนหรือไม่
            if not myku_username or not myku_password:
                raise ValidationError("MyKU credentials are not available for the user.")
            if not user.is_authenticated:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

            # ใช้ username และ password ที่ดึงมาจากฐานข้อมูลเพื่อเข้าสู่ระบบ MyKU
            client = Client(username=myku_username, password=myku_password)
            client.login()  # Login ด้วยข้อมูลที่มี

            # ดึงข้อมูลของนักศึกษาจาก MyKU
            student_data = client.fetch_student_personal()
            schedule_data = client.fetch_schedule()
            announce_data = client.fetch_announce()
            grades_data = client.fetch_grades()
            group_course_data = client.fetch_group_course()
            student_education_data = client.fetch_student_education()
            gpax_data = client.fetch_gpax()

            # เตรียมข้อมูลสำหรับการตอบกลับ
            response_data = {
                'student_data': student_data,
                'results': {
                    'schedule_data': schedule_data if schedule_data else [],
                    'announce_data': announce_data if announce_data else [],
                    'grades_data': grades_data if grades_data else [],
                    'group_course_data': group_course_data if group_course_data else [],
                    'student_education_data': student_education_data if student_education_data else None,
                    'gpax_data': gpax_data if gpax_data else []
                },
                'message': 'Successfully fetched all MyKU data.'
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in MykuDataView: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RegisterUserView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    def post(self, request):
        user_data = request.data
        email = user_data.get('email')

        # ตรวจสอบและลบ OTP และผู้ใช้ที่ยังไม่ยืนยัน
        try:
            existing_user = User.objects.get(email=email, is_verified=False)

            # ลบ OTP ที่เกี่ยวข้องกับผู้ใช้ก่อนลบผู้ใช้
            OneTimePassword.objects.filter(user=existing_user).delete()

            # ลบผู้ใช้ที่ไม่ยืนยัน
            existing_user.delete()
        except User.DoesNotExist:
            pass  # ถ้าไม่มีผู้ใช้ที่ยังไม่ยืนยันก็ข้ามไป

        # สร้างผู้ใช้ใหม่และส่ง OTP ใหม่
        serializer = self.serializer_class(data=user_data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save(is_active=False, is_verified=False)  # ผู้ใช้ยังไม่พร้อมใช้งาน
            send_code_to_user(user.email)  # ส่ง OTP ใหม่

            return Response({
                'message': 'Registration successful. OTP sent to your email.'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyUserEmail(GenericAPIView):
    serializer_class = VerifyOtpSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email, is_verified=False)
            otp_record = OneTimePassword.objects.get(user=user, code=otp)

            user.is_verified = True
            user.is_active = True  # เปิดใช้งานผู้ใช้
            user.save()
            otp_record.delete()  # ลบ OTP หลังจากยืนยัน

            return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)

        except (User.DoesNotExist, OneTimePassword.DoesNotExist):
            return Response({'message': 'Invalid OTP or email.'}, status=status.HTTP_400_BAD_REQUEST)
        
class ResendOtpView(GenericAPIView):
    serializer_class = EmailSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                OneTimePassword.objects.filter(user=user).delete()
                send_code_to_user(email)
                return Response({'message': 'OTP has been resent!'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'message': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginUserView(GenericAPIView):
    serializer_class = LoginUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # ดึง refresh และ access tokens จาก serializer
        refresh = serializer.validated_data.get('refresh_token')
        access = serializer.validated_data.get('access_token')

        # สร้าง response พร้อมข้อมูล
        response = Response(serializer.data, status=status.HTTP_200_OK)

        # ตั้งคุกกี้สำหรับ refresh และ access tokens
        response.set_cookie('refresh', refresh, httponly=True)
        response.set_cookie('access', access, httponly=True)

        return response

class TestAuthenticationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            'msg': 'its works'
        }
        return Response(data, status=status.HTTP_200_OK)

class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response({'message': "a link has been sent to your email to reset your password"}, status=status.HTTP_200_OK)

class PasswordResetConfirm(GenericAPIView):
    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'message': 'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({'success': True, 'message': 'credentials valid', 'uidb64': uidb64, 'token': token}, status=status.HTTP_200_OK)
        except DjangoUnicodeDecodeError as e:
            return Response({'message': 'token is invalid or has expired'}, status=status.HTTP_401_UNAUTHORIZED)

class SetNewPasswordView(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': 'password reset successful'}, status=status.HTTP_200_OK)

class LogoutUserView(GenericAPIView):
    serializer_class = LogoutUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                return Response({'message': 'An error occurred during logout'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        response = Response({'message': 'logout successful'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh')
        response.delete_cookie('access')
        return response

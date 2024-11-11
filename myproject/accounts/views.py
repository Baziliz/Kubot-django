from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from .serializers import UserRegisterSerializer, LoginUserSerializer, SetNewPasswordSerializer, PasswordResetRequestSerializer, LogoutUserSerializer, EmailSerializer, VerifyOtpSerializer
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from .utils import send_code_to_user
from .models import OneTimePassword, User, StudentProfile, Schedule, Grade, GroupCourse, StudentEducation, GPAX, Announcement, DiscordProfile, TeacherProfile, TeachingSchedule, Event, Announcement
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect, get_object_or_404
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

from .serializers import LoginWithMykuSerializer, DiscordConnectSerializer, StudentProfileSerializer, TeacherRegistrationSerializer, UserProfileSerializer, GroupCourseSerializer, TeachingScheduleSerializer, EventSerializer, AnnouncementSerializer

User = get_user_model()
import requests
import environ
env = environ.Env()
environ.Env.read_env()

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        print("User role:", user.role)  # Debug: พิมพ์ค่า role ที่ได้ออกมา
        return Response(serializer.data, status=status.HTTP_200_OK)

class StudentDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return Response({"error": "Only students can access this data."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            student_profile = StudentProfile.objects.get(user=request.user)
            data = {
                "std_id": student_profile.std_id,
                "name_th": student_profile.name_th,
                "name_en": student_profile.name_en,
                "birth_date": student_profile.birth_date,
                "gender": student_profile.gender,
                "email": student_profile.email,
            }
            return Response(data, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response({"error": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)

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

        return redirect('http://localhost:5173/connections?discord_connected=true')

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
        
class DiscordLogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def post(self, request):
        try:
            # Delete the Discord profile associated with the user
            profile = DiscordProfile.objects.get(user=request.user)
            profile.delete()

            return Response({"message": "Successfully disconnected from Discord"}, status=200)
        except DiscordProfile.DoesNotExist:
            return Response({"error": "Discord profile not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


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
                
                std_code = gpax_data['results'][0]['std_code']

                # ดึงหรือสร้าง StudentProfile จาก User
                student_results = student_data['results']['stdPersonalModel']
                student_profile, created = StudentProfile.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'std_id': student_results['stdId'],
                        'std_code': std_code,
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
                for semester_data in grades_data['results']:
                    academic_year = semester_data['academicYear']
                    gpa = semester_data['gpa']
                    total_credits = semester_data['cr']

                    for course in semester_data['grade']:
                        Grade.objects.update_or_create(
                            student_profile=student_profile,
                            academic_year=academic_year,
                            semester=course['registration_semester'],
                            subject_code=course['subject_code'],
                            defaults={
                                'subject_name_th': course['subject_name_th'],
                                'subject_name_en': course['subject_name_en'],
                                'credit': course['credit'],
                                'grade': course['grade'],
                                'gpa': gpa, 
                                'total_credits': total_credits  
                            }
                        )

                # บันทึกข้อมูลกลุ่มวิชา (GroupCourse)
                if group_course_data and 'results' in group_course_data:
                    for group in group_course_data['results']:
                        period_date = group.get('peroid_date', 'N/A')  # กำหนดค่า default หากไม่มีข้อมูล
                        for course in group.get('course', []):  # ตรวจสอบว่ามี course ใน group ก่อนดำเนินการ
                            GroupCourse.objects.update_or_create(
                                student_profile=student_profile,
                                subject_code=course.get('subject_code', 'N/A'),  # กำหนดค่า default หากไม่มีข้อมูล
                                defaults={
                                    'period_date': period_date,
                                    'subject_name': course.get('subject_name_th', 'N/A'),
                                    'teacher_name': course.get('teacher_name', 'N/A'),
                                    'day_w': course.get('day_w', 'N/A'),
                                    'room_name_th': course.get('room_name_th', 'N/A'),
                                    'time_from': course.get('time_from', 'N/A'),
                                    'time_to': course.get('time_to', 'N/A'),
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
                    'std_code': std_code,
                    'group_course_data': group_course_data,
                    'schedule_data': schedule_data,
                    'message': 'Successfully linked MyKU and saved all data.'
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MykuDataView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # ดึงโปรไฟล์ของผู้ใช้งานที่ล็อกอิน
            user = request.user
            student_profile = StudentProfile.objects.get(user=user)

            # ดึงข้อมูลที่เกี่ยวข้องจากฐานข้อมูล
            schedules = Schedule.objects.filter(student_profile=student_profile)
            group_courses = GroupCourse.objects.filter(student_profile=student_profile)
            grades = Grade.objects.filter(student_profile=student_profile)
            student_education = StudentEducation.objects.filter(student_profile=student_profile).first()
            gpax = GPAX.objects.get(student_profile=student_profile)

            # จัดกลุ่มเกรดตามปีการศึกษาและภาคการศึกษา
            grouped_grades = {}
            for grade in grades:
                key = f"{grade.academic_year} - ภาค {grade.semester}"
                if key not in grouped_grades:
                    grouped_grades[key] = {
                        'gpa': grade.gpa,
                        'total_credits': grade.total_credits,
                        'courses': [],
                    }
                grouped_grades[key]['courses'].append({
                    'subject_code': grade.subject_code,
                    'subject_name_th': grade.subject_name_th,
                    'subject_name_en': grade.subject_name_en,
                    'credit': grade.credit,
                    'grade': grade.grade,
                })

            # เรียงลำดับปีการศึกษาและภาคการศึกษาให้ใหม่ขึ้นก่อน
            sorted_grades = dict(sorted(
                grouped_grades.items(), 
                key=lambda x: (int(x[0].split('/')[0]), int(x[0].split(' ')[-1])), 
                reverse=True
            ))

            # เตรียมข้อมูลเพื่อตอบกลับ
            response_data = {
                'student_profile': {
                    'std_code': student_profile.std_code,
                    'name_th': student_profile.name_th,
                    'name_en': student_profile.name_en,
                    'birth_date': student_profile.birth_date,
                    'gender': student_profile.gender,
                    'religion': student_profile.religion,
                    'phone': student_profile.phone,
                    'email': student_profile.email,
                    'ku_email': student_profile.ku_email or "",
                },
                'grades_data': sorted_grades,
                'schedule_data': [
                    {'academic_year': s.academic_year, 'semester': s.semester} for s in schedules
                ],
                'group_course_data': [
                    {
                        'subject_code': g.subject_code,
                        'subject_name': g.subject_name,
                        'teacher_name': g.teacher_name,
                        'day_w': g.day_w,
                        'room_name_th': g.room_name_th,
                        'time_from': g.time_from,
                        'time_to': g.time_to,
                    }
                    for g in group_courses
                ],
                'student_education_data': {
                    'faculty_name_th': student_education.faculty_name_th,
                    'major_name_th': student_education.major_name_th,
                    'status': student_education.status,
                    'degree_name': student_education.degree_name,
                } if student_education else None,
                'gpax_data': {
                    'gpax': gpax.gpax,
                    'total_credit': gpax.total_credit,
                },
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except StudentProfile.DoesNotExist:
            return Response({'error': 'Student profile not found'}, status=status.HTTP_404_NOT_FOUND)
        except GPAX.DoesNotExist:
            return Response({'error': 'GPAX data not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DisconnectMykuDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            student_profile = StudentProfile.objects.get(user=user)

            # ตั้งค่าโปรไฟล์เป็นว่างแทนการลบข้อมูลเพื่อไม่ให้มีการเชื่อมโยงกับระบบอีกต่อไป
            student_profile.std_id = ""
            student_profile.std_code = ""
            student_profile.save()

            return Response(
                {"detail": "Your Nontri connection has been successfully disconnected."},
                status=status.HTTP_200_OK
            )
        except StudentProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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

            # Check OTP expiration
            expiration_time = otp_record.created_at + timedelta(minutes=5)
            if now() > expiration_time:
                otp_record.delete()  # Delete expired OTP
                return Response({'message': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)

            # OTP is valid, proceed with verification
            user.is_verified = True
            user.is_active = True  # Activate user
            user.save()
            otp_record.delete()  # Delete OTP after verification

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

        validated_data = serializer.validated_data
        refresh = validated_data.get('refresh_token')
        access = validated_data.get('access_token')
        role = validated_data.get('role')

        response = Response(validated_data, status=status.HTTP_200_OK)
        
        response.set_cookie('refresh', refresh, httponly=True)
        response.set_cookie('access', access, httponly=True)

        return response

class TestAuthenticationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}",
            'role': user.role,  # assuming 'role' is a field in your User model
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
    
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            student_profile = request.user.student_profile  # ดึงข้อมูลโปรไฟล์จากผู้ใช้
        except StudentProfile.DoesNotExist:
            return Response({"error": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = StudentProfileSerializer(student_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AdminCreateTeacherView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Only admin can create teacher accounts."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TeacherRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Teacher account created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GroupCourseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # ตรวจสอบบทบาทผู้ใช้ หากไม่ใช่อาจารย์จะปฏิเสธการเข้าถึง
        if request.user.role != 'teacher':
            return Response({"error": "Only teachers can create group courses."}, status=status.HTTP_403_FORBIDDEN)
        
        # ใช้ Serializer จัดการข้อมูลที่รับมา
        serializer = GroupCourseSerializer(data=request.data)
        if serializer.is_valid():
            group_course = serializer.save()

            # เชื่อมโยง teacher โดยอัตโนมัติหลังจากสร้าง
            if group_course.teacher_name:
                try:
                    teacher_profile = TeacherProfile.objects.get(full_name=group_course.teacher_name)
                    group_course.teacher = teacher_profile
                    group_course.save()
                except TeacherProfile.DoesNotExist:
                    pass  # หากไม่พบ TeacherProfile จะข้ามไป
            
            return Response({"message": "GroupCourse created successfully"}, status=status.HTTP_201_CREATED)
        
        # กรณีข้อมูลไม่ถูกต้อง
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeachingScheduleListCreateView(generics.ListCreateAPIView):
    queryset = TeachingSchedule.objects.all()
    serializer_class = TeachingScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

class TeachingScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TeachingSchedule.objects.all()
    serializer_class = TeachingScheduleSerializer
    permission_classes = [IsAuthenticated]

class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        schedule_id = self.request.data.get("schedule")
        try:
            schedule = TeachingSchedule.objects.get(id=schedule_id, teacher=self.request.user)
            serializer.save(schedule=schedule)
        except TeachingSchedule.DoesNotExist:
            raise serializers.ValidationError({"schedule": "Invalid or unauthorized schedule selection."})

class AnnouncementListCreateView(generics.ListCreateAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        schedule_id = self.kwargs['schedule_id']
        return Announcement.objects.filter(schedule_id=schedule_id)

    def perform_create(self, serializer):
        schedule = TeachingSchedule.objects.get(id=self.kwargs['schedule_id'])
        serializer.save(schedule=schedule)

class TeacherCourseListView(generics.ListAPIView):
    serializer_class = GroupCourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ใช้ TeacherProfile ของผู้ใช้ที่ล็อกอินอยู่
        teacher_profile = TeacherProfile.objects.get(user=self.request.user)
        return GroupCourse.objects.filter(teacher=teacher_profile)
    
class EventListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        event.delete()
        return Response({"detail": "Deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
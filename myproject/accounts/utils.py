import random
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, OneTimePassword
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now, timedelta

def generateOtp():
    otp = ""
    for i in range(6):
        otp += str(random.randint(1, 9))
    return otp

def send_code_to_user(email):
    Subject = "One-Time Passcode for Email Verification"
    otp_code = generateOtp()
    print(f"Generated OTP: {otp_code}")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise ValueError("User with this email does not exist.")

    # ลบ OTP เดิมหากมีอยู่
    OneTimePassword.objects.filter(user=user).delete()

    # ตรวจสอบคูลดาวน์ (กรณีต้องการ)
    recent_otp = OneTimePassword.objects.filter(user=user, created_at__gte=now() - timedelta(minutes=5))
    if recent_otp.exists():
        raise Exception("Please wait a few minutes before requesting a new OTP.")

    # สร้าง OTP ใหม่และบันทึกลงฐานข้อมูล
    OneTimePassword.objects.create(user=user, code=otp_code)

    # เนื้อหาอีเมล
    email_body = format_html(
        '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
                <h2 style="color: #333; text-align: center;">OTP Verification</h2>
                <p style="color: #555; text-align: center;">Hi <strong>{first_name}</strong>,</p>
                <p style="color: #555; text-align: center;">Enter this OTP to verify your email:</p>
                <div style="font-size: 24px; font-weight: bold; color: #333; text-align: center; margin: 20px 0;">
                    {otp_code}
                </div>
                <p style="color: #555; text-align: center;">If you didn't request this, please ignore.</p>
                <p style="color: #555; text-align: center;">Regards,<br>KU-Bot Team</p>
            </div>
        ''',
        first_name=user.first_name,
        otp_code=otp_code
    )

    from_email = settings.DEFAULT_FROM_EMAIL
    print(f"Sending email to {email} from {from_email}")

    send_email = EmailMessage(subject=Subject, body=email_body, from_email=from_email, to=[email])
    send_email.content_subtype = "html"

    try:
        send_email.send(fail_silently=False)
        print(f"Email sent successfully to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        raise

def send_normal_email(data):
    email = EmailMessage(
        subject=data['email-subject'],
        body=data['email_body'],
        from_email=settings.EMAIL_HOST_USER,
        to=[data['to_email']]
    )
    try:
        email.send()
        print(f"Normal email sent successfully to {data['to_email']}")
    except Exception as e:
        print(f"Failed to send normal email to {data['to_email']}: {e}")

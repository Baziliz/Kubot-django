from django.urls import path, include
from .views import RegisterUserView, VerifyUserEmail, LoginUserView, TestAuthenticationView, PasswordResetConfirm, PasswordResetRequestView, SetNewPasswordView, LogoutUserView, RegisterAndLoginStudentView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import MykuLoginView

urlpatterns=[
    path('register/', RegisterUserView.as_view(), name = 'register'),
    path('verify-email/', VerifyUserEmail.as_view(), name = 'verify-email'),
    path('login/', LoginUserView.as_view(), name = 'login'),
    path('profile/', TestAuthenticationView.as_view(), name = 'granted'),
    path('token/refresh/', TokenRefreshView.as_view(), name = 'refresh-token'),
    path('password-reset/', PasswordResetRequestView.as_view(), name = 'password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name = 'password-reset-confirm'),
    path('set-new-password/', SetNewPasswordView.as_view(), name = 'set-new-password'),
    path('logout/', LogoutUserView.as_view(), name = 'logout'),
    path('register-and-login-student/', RegisterAndLoginStudentView.as_view(), name='register_and_login_student'),
    path('myku-login/', MykuLoginView.as_view(), name='myku-login'),
]

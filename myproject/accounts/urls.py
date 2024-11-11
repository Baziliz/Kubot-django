from django.urls import path, include
from .views import RegisterUserView, VerifyUserEmail, LoginUserView, TestAuthenticationView, PasswordResetConfirm, PasswordResetRequestView, SetNewPasswordView, LogoutUserView, ResendOtpView
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from .views import MykuLoginView, MykuDataView, DiscordConnectView, DiscordCallbackView, DiscordProfileView, StudentDataView, DiscordLogoutView, DisconnectMykuDataView, UpdateProfileView, AdminCreateTeacherView, UserProfileView
from .views import TeachingScheduleListCreateView, TeachingScheduleDetailView, EventListCreateView, AnnouncementListCreateView, TeacherCourseListView, EventListView, EventCreateView, EventUpdateView, EventDeleteView

urlpatterns=[
    path('register/', RegisterUserView.as_view(), name = 'register'),
    path('verify-email/', VerifyUserEmail.as_view(), name = 'verify-email'),
    path('resend-otp/', ResendOtpView.as_view(), name='resend-otp'),
    path('login/', LoginUserView.as_view(), name = 'login'),
    path('profile/', TestAuthenticationView.as_view(), name = 'granted'),
    path('token/refresh/', TokenRefreshView.as_view(), name = 'refresh-token'),
    path('password-reset/', PasswordResetRequestView.as_view(), name = 'password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name = 'password-reset-confirm'),
    path('set-new-password/', SetNewPasswordView.as_view(), name = 'set-new-password'),
    path('logout/', LogoutUserView.as_view(), name = 'logout'),
    path('myku-login/', MykuLoginView.as_view(), name='myku-login'),
    path('myku-data/', MykuDataView.as_view(), name='myku-data'),
    path('disconnect-myku-data/', DisconnectMykuDataView.as_view(), name='delete-myku-data'),
    path('discord/connect/', DiscordConnectView.as_view(), name='discord-connect'),
    path('discord/callback/', DiscordCallbackView.as_view(), name='discord-callback'),
    path('discord/profile/', DiscordProfileView.as_view(), name='discord-profile'),
    path('discord/logout/', DiscordLogoutView.as_view(), name='discord-logout'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('student-data/', StudentDataView.as_view(), name='student-data'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('admin/create-teacher/', AdminCreateTeacherView.as_view(), name='admin_create_teacher'),
    path('user-profile/', UserProfileView.as_view(), name='user-profile'),
    path('schedules/', TeachingScheduleListCreateView.as_view(), name='schedule-list-create'),
    path('schedules/<int:pk>/', TeachingScheduleDetailView.as_view(), name='schedule-detail'),
    path('event/', EventListCreateView.as_view(), name='event-list-create'),
    path('schedules/<int:schedule_id>/announcements/', AnnouncementListCreateView.as_view(), name='announcement-list-create'),
    path('teacher/courses/', TeacherCourseListView.as_view(), name='teacher_courses'),
    path('event/create/', EventCreateView.as_view(), name='event-create'),
    path('event/list/', EventListView.as_view(), name='event-list'),
    path('event/update/<int:pk>/', EventUpdateView.as_view(), name='event-update'),
    path('event/delete/<int:pk>/', EventDeleteView.as_view(), name='event-delete'),
]


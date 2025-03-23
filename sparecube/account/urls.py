from django.urls import path
from .views import (
    UserAPIView,
    UsersAPIView,
    CreateUserAPIView,
    LoginUserAPIView,
    PasswordAPIView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Users
    path('login/',          LoginUserAPIView.as_view(),         name="login"),
    path('signup/',         CreateUserAPIView.as_view(),        name="signup"),
    path('refresh/',        TokenRefreshView.as_view(),         name="token_refresh"),

    path('user/',           UserAPIView.as_view(),              name="users"),
    path('user/all',        UsersAPIView.as_view(),           name="users"),
    path('user/password/',  PasswordAPIView.as_view(),          name="password-recovery"),
]
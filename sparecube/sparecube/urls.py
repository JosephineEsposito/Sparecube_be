#@author: josephineesposito
#2025

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls import include
import os

ver = os.environ["VER"]


from .views import (
    HelloAPIView,
    DBTestApiView
)


urlpatterns = [
    path(f'api/{ver}/', include('account.urls')),
    path(f'api/{ver}/', include('locker.urls')),
    path('admin/', admin.site.urls),

    path(f'api/{ver}/ping/', HelloAPIView.as_view()),
    path(f'api/{ver}/database/', DBTestApiView.as_view()),
]

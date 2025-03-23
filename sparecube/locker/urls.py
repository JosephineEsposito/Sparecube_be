from django.urls import path

from .views import (
    LocationAPIView,
    LocationsAPIView,
    LockerAPIView,
    LockersAPIView,
    DrawerAPIView,
    DrawersAPIView,
    BookingAPIView,
    BookingsAPIView,
    BookLocAPIView,
    LogAPIView,
)


urlpatterns = [
    path('location/',           LocationAPIView.as_view(),      name="location"),
    path('location/all/',       LocationsAPIView.as_view(),     name="location"),
    path('location/<int:id>',   LocationAPIView.as_view(),      name="location"),

    path('locker/',             LockerAPIView.as_view(),        name='locker'),
    path('locker/all/',         LockersAPIView.as_view(),       name='locker'),
    path('locker/<int:id>',     LockerAPIView.as_view(),        name='locker'),

    path('drawer/',             DrawerAPIView.as_view(),        name='drawer'),
    path('drawer/all/',         DrawersAPIView.as_view(),       name='drawer'),
    path('drawer/<int:id>',     DrawerAPIView.as_view(),        name='drawer'),
    
    path('booking/',            BookingAPIView.as_view(),       name='booking'),
    path('booking/all/',        BookingsAPIView.as_view(),      name='booking'),
    path('booking/all/join/',    BookLocAPIView.as_view(),       name='booking'),
    path('booking/<int:id>',    BookingAPIView.as_view(),       name='booking'),
    
    path('log/',                LogAPIView.as_view(),           name='logs'),
]

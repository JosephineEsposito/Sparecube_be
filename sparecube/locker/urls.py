from django.urls import path

from .views import (
    LocationAPIView,
    LocationsAPIView,
    TowerAPIView,
    TowersAPIView,
    LockerAPIView,
    LockersAPIView,
    DrawerAPIView,
    DrawersAPIView,
    DrawerFiltered,
    BookingAPIView,
    BookingsAPIView,
    BookLocAPIView,
    BookStatusAPIView,
    TowersDrawersAPIView,
    LogAPIView,
)


urlpatterns = [
    path('location/',           LocationAPIView.as_view(),      name="location"),
    path('location/all/',       LocationsAPIView.as_view(),     name="location"),
    path('location/<int:id>',   LocationAPIView.as_view(),      name="location"),


    path('tower/',              TowerAPIView.as_view(),         name='tower'),
    path('tower/all/',          TowersAPIView.as_view(),        name='tower'),
    path('tower/<int:id>',      TowerAPIView.as_view(),         name='tower'),


    path('locker/',             LockerAPIView.as_view(),        name='locker'),
    path('locker/all/',         LockersAPIView.as_view(),       name='locker'),
    path('locker/<int:id>',     LockerAPIView.as_view(),        name='locker'),


    path('drawer/',             DrawerAPIView.as_view(),        name='drawer'),
    path('drawer/all/',         DrawersAPIView.as_view(),       name='drawer'),
    path('drawer/<int:id>',     DrawerAPIView.as_view(),        name='drawer'),

    path('drawer/all/filtered/',DrawerFiltered.as_view(),       name='drawer'),
    

    path('booking/',            BookingAPIView.as_view(),       name='booking'),
    path('booking/all/',        BookingsAPIView.as_view(),      name='booking'),
    path('booking/<int:id>',    BookingsAPIView.as_view(),      name='booking'),

    path('booking/status/',     BookingAPIView.as_view(),       name='booking'),

   # path('booking/status/',     BookStatusAPIView.as_view(),    name='booking'),



    path('booking/all/join/',   BookLocAPIView.as_view(),       name='booking'),
    path('drawer/all/join/',    TowersDrawersAPIView.as_view(), name='booking'),


    path('log/',                LogAPIView.as_view(),           name='logs'),
]

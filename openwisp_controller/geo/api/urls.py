from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^api/device-mobile-location/(?P<pk>[^/]+)/$',
        views.mobile_location,
        name='api_mobile_location'),
]

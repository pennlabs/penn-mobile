from rest_framework import routers

from django.urls import path, include

from booking.views import UserViewSet, GroupMembershipViewSet, GroupViewSet

router = routers.DefaultRouter()

router.register(r'users', UserViewSet)
router.register(r'membership', GroupMembershipViewSet)
router.register(r'groups', GroupViewSet)

urlpatterns = [
    path(r'', include(router.urls))
]

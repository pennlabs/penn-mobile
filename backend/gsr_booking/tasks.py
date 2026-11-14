import logging

from celery import shared_task

from gsr_booking.models import GSRBookingShare
from user.models import AndroidNotificationToken, IOSNotificationToken, NotificationService
from user.notifications import (
    android_send_notification,
    ios_send_dev_notification,
    ios_send_notification,
)


logger = logging.getLogger(__name__)


@shared_task(name="gsr_booking.send_gsr_booking_invite_notification")
def send_gsr_booking_invite_notification(share_id):
    share = GSRBookingShare.objects.select_related("inviter", "recipient").get(pk=share_id)
    if share.status != GSRBookingShare.PENDING or not share.is_relevant():
        return

    inviter_name = share.inviter.get_full_name() or share.inviter.username
    title = "GSR booking invitation"
    body = f"{inviter_name} invited you to a GSR booking. Open Penn Mobile to respond."
    service = NotificationService.objects.filter(name="PENN_MOBILE").first()
    if service is None:
        logger.error("Cannot notify GSR invitee: PENN_MOBILE notification service is missing.")
        return

    enabled_users = service.enabled_users.filter(pk=share.recipient_id)
    if not enabled_users.exists():
        return

    notification_targets = (
        (
            IOSNotificationToken.objects.filter(user__in=enabled_users, is_dev=False),
            ios_send_notification,
        ),
        (
            IOSNotificationToken.objects.filter(user__in=enabled_users, is_dev=True),
            ios_send_dev_notification,
        ),
        (
            AndroidNotificationToken.objects.filter(user__in=enabled_users),
            android_send_notification,
        ),
    )
    for tokens, send_notification in notification_targets:
        token_values = list(tokens.values_list("token", flat=True))
        if token_values:
            send_notification.delay(token_values, title, body, False)

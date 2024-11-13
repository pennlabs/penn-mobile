from typing import Optional

from celery import shared_task
from django.contrib.auth.models import Group
from django.core.mail import send_mail as django_send_mail
from django.template.loader import get_template


@shared_task(name="utils.send_mail")
def send_mail(
    subject: str,
    recipient_list: Optional[list[str]] = None,
    message: Optional[str] = None,
    html_message: Optional[str] = None,
) -> int:
    if recipient_list is None:
        raise ValueError("Recipient list cannot be None")
    success = django_send_mail(
        subject=subject,
        message=message if message else "",
        from_email=None,
        recipient_list=recipient_list,
        fail_silently=False,
        html_message=html_message,
    )
    return success
    # TODO: log upon failure!


@shared_task(name="utils.send_automated_email")
def send_automated_email(subject: str, recipient_list: Optional[list[str]], message: str) -> bool:
    template = get_template("email.html")
    html_message = template.render({"message": message})
    return send_mail(subject, recipient_list, html_message=html_message)


def get_backend_manager_emails() -> list[str]:
    if group := Group.objects.filter(name="backend_managers").first():
        return list(
            group.user_set.exclude(email="")
            .exclude(email__isnull=True)
            .values_list("email", flat=True)
        )
    return []

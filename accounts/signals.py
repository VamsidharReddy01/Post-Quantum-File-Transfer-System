from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .services.audit_service import log_action


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    log_action(user, "Login", request)


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    if user:
        log_action(user, "Logout", request)

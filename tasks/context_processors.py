from .models import Notification, Profile


def notification_count(request):
    """Add unread notification count to template context."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notification_count': count}
    return {'unread_notification_count': 0}


def user_profile(request):
    """Add current user's profile (with avatar) to template context."""
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        return {'user_profile': profile}
    return {'user_profile': None}

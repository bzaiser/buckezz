from .models import UserSetting

def user_settings(request):
    if request.user.is_authenticated:
        settings, _ = UserSetting.objects.get_or_create(user=request.user)
        return {'user_settings': settings}
    return {'user_settings': None}

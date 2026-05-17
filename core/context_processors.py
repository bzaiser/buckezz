from django.contrib.auth.models import User
from .models import UserSetting

def user_settings(request):
    if request.user.is_authenticated:
        settings, _ = UserSetting.objects.get_or_create(user=request.user)
        return {'user_settings': settings}
    
    # Fallback to the main admin's settings for guests
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        settings, _ = UserSetting.objects.get_or_create(user=admin_user)
        return {'user_settings': settings}
        
    return {'user_settings': None}

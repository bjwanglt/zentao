from django.apps import AppConfig


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        from utils.user_info_cache import user_info_cache
        user_info_cache(user_id=None)
        from web import handlers

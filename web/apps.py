from django.apps import AppConfig
from utils.user_info_cache import user_info_cache


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        user_info_cache(9)
        from web.handlers import insert_into_user_cache

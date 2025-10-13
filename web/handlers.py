import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.dispatch.dispatcher import receiver
from utils.user_info_cache import user_info_cache
from django.db.models.signals import post_save
from web.models import UserInfo, Issues

from redis import Redis
from django_redis import get_redis_connection


# 用户注册 缓存用户信息
@receiver(post_save, sender=UserInfo)
def insert_into_user_cache(sender, instance, created, **kwargs):
    if created:
        user_info_cache(user_id=instance.id)


# 问题指派，即时通知被指派人
@receiver(post_save, sender=Issues)
def send_msg(sender, instance, created, **kwargs):
    if created:
        # 发送即时消息提醒
        cache: Redis = get_redis_connection('offline_msgs')
        cache.lpush(f'msg_{instance.assign_id}', instance.subject)
        offline_msgs_decode = cache.lrange(f'msg_{instance.assign_id}', 0, -1)
        offline_msgs = list(enumerate(map(lambda x: x.decode('utf-8'), offline_msgs_decode)))
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.assign_id}",
            {
                'type': 'send.message',
                'message': json.dumps(offline_msgs)
            }
        )

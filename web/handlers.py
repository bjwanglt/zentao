import json

from django.dispatch.dispatcher import receiver
from utils.user_info_cache import user_info_cache
from django.db.models.signals import post_save, pre_save
from web.models import UserInfo, Issues
from django.conf import settings
from redis import Redis

from redis import Redis
from django_redis import get_redis_connection
from uuid import uuid4
from django.urls import reverse


# 用户注册 缓存用户信息
@receiver(post_save, sender=UserInfo)
def insert_into_user_cache(sender, instance, created, **kwargs):
    if created:
        user_info_cache(user_id=instance.id)


def savemsg_and_publish(user_id, subject):
    cache: Redis = get_redis_connection('offline_msgs')
    # 新消息入库
    cache.hset(f'msg_{user_id}', key=str(uuid4()), value=subject)
    # 获取所有历史未读消息 并 发送
    '''
    channel_layer = get_channel_layer()
    data = {k.decode('utf-8'): v.decode('utf-8') for k, v in cache.hgetall(f'msg_{user_id}').items()}
    offline_msgs = list(data.items())
    async_to_sync(channel_layer.group_send)(f'user_{user_id}', {
        'type': 'send.message',
        'message': json.dumps(offline_msgs)
    })
    '''
    # 发布待通知用户ID
    cache.publish('websocket_events', json.dumps(dict(
        user_id=user_id,
        type='notice'
    )))


# 问题指派，即时通知被指派人
@receiver(pre_save, sender=Issues)
def send_msg_for_update(sender, instance, **kwargs):
    if instance.pk:
        # 数据修改
        old_assign = Issues.objects.filter(id=instance.pk).values_list('assign_id', flat=True).first()
        new_assign = instance.assign_id
        if old_assign != new_assign:
            link_url = reverse('web:issue_detail', kwargs=dict(pid=instance.project_id, issue_id=instance.id))
            cache:Redis = get_redis_connection('default')
            user_name = cache.hget(settings.USER_INFO_CACHE_PREFIX+str(instance.creator_id),'username')
            savemsg_and_publish(new_assign, f'<a href="{link_url}">{user_name.decode("utf-8")}给你指派了一个新的问题，请及时处理</a>')


@receiver(post_save, sender=Issues)
def send_msg_for_create(sender, instance, created, **kwargs):
    # 数据新建
    if created:
        user_id = instance.assign_id
        link_url = reverse('web:issue_detail', kwargs=dict(pid=instance.project_id, issue_id=instance.id))
        cache: Redis = get_redis_connection('default')
        user_name = cache.hget(settings.USER_INFO_CACHE_PREFIX + str(instance.creator_id), 'username')
        savemsg_and_publish(user_id, f'<a href="{link_url}">【{user_name.decode("utf-8")}】给你指派了一个新的问题，请即时处理</a>')

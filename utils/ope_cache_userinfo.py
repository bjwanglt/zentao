from django_redis import get_redis_connection
from web import models
from redis import Redis


class OpeCacheUserInfo:
    PREFIX = 'sys_cache_user_info_'
    redis_conn: Redis = get_redis_connection()
    raw_sql = '''
        select
            uu.id,
            pp.project_num ,
            pp.project_member ,
            pp.per_file_size,
            pp.project_space,
            uu.username
        from
            user_info uu
        left join price_policy pp on
            uu.price_policy_id = pp.id
        '''

    def get_user_info(self, user_id):
        user_info_bytedict = self.redis_conn.hgetall(f'{self.PREFIX}{str(user_id)}')
        if user_info_bytedict:
            return {k.decode('utf-8'): int(v.decode('utf-8')) for k, v in user_info_bytedict.items()}

    def get_user_projectnum(self, user_id):
        user_info = self.get_user_info(user_id)
        if user_info:
            return user_info.get('project_num')

    def get_user_projectmember(self, user_id):
        user_info = self.get_user_info(user_id)
        if user_info:
            return user_info.get('project_member')

    def get_user_perfilesize(self, user_id):
        user_info = self.get_user_info(user_id)
        if user_info:
            return user_info.get('per_file_size') * 1024 * 1024

    def get_user_projectspace(self, user_id):
        user_info = self.get_user_info(user_id)
        if user_info:
            return user_info.get('project_space') * 1024 * 1024

    def refresh_all_user_info(self):
        """刷新全部user_info缓存"""
        objs = models.UserInfo.objects.raw(self.raw_sql)
        pipe = self.redis_conn.pipeline()
        for obj in objs:
            pipe.hset(self.PREFIX + str(obj.id), mapping={
                'project_num': obj.project_num,
                'project_member': obj.project_member,
                'per_file_size': obj.per_file_size,
                'project_space': obj.project_space,
                'username': obj.username,
            })
        pipe.execute()

    def update_user_info(self, *, user_id=None, project_num=None, project_member=None, per_file_size=None,
                         project_space=None):
        """关键字传参，修改成功返回 1 否则返回 0；[修改数字需和数据库保持一致，否则操作无效 (待修复)]"""
        if not user_id:
            return 0
        source_kwargs = {'project_num': project_num, 'project_member': project_member, 'per_file_size': per_file_size,
                         'project_space': project_space}
        effective_kwargs = {k: v for k, v in source_kwargs.items() if v}
        if not effective_kwargs:
            return 0
        self.redis_conn.hset(f'{self.PREFIX}{str(user_id)}', mapping=effective_kwargs)
        return 1

        # exists = models.UserInfo.objects.filter(id=user_id, **effective_kwargs).exists()
        # if exists:
        #     self.redis_conn.hset(f'{self.PREFIX}{str(user_id)}', mapping=effective_kwargs)
        #     return 1
        # return 0


ope_cache_userinfo = OpeCacheUserInfo()

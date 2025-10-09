from redis import Redis


def user_info_cache(user_id=None):
    from django_redis import get_redis_connection
    # 防止ready重复执行，导致数据重复初始化的问题
    redis_conn: Redis = get_redis_connection()
    if not redis_conn.set('user_info_cache_lock', 1, nx=True, ex=30):
        return
    from web import models
    raw_sql = '''
            select
            	uu.id,
            	pp.project_num , # 项目个数
            	pp.project_member ,  # 项目参与人数
            	pp.per_file_size, # 单文件大小限制
            	pp.project_space # 总空间大小
            from
            	user_info uu
            left join price_policy pp on
            	uu.price_policy_id = pp.id
            ''' + f' where uu.id = {user_id}' if user_id else ''
    objs = models.UserInfo.objects.raw(raw_sql)

    pipe = redis_conn.pipeline()
    for obj in objs:
        pipe.hset('sys_cache_user_info_' + str(obj.id), mapping={
            'project_num': obj.project_num,
            'project_member': obj.project_member,
            'per_file_size': obj.per_file_size,
            'project_space': obj.project_space,
        })
    pipe.execute()
    print('用户信息缓存完毕')

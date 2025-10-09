LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_TZ = False

# mysql配置
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.mysql',
        # django.db.backends.mysql   django.db.backends.base.base.BaseDatabaseWrapper
        'NAME': 'zentao',
        'USER': 'root',
        'PASSWORD': 'mysql123',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,  # 最小连接数
            'MAX_OVERFLOW': 10,  # 在最小的基础上，还可以增加10个，即：最大20个
            'RECYCLE': 24 * 60 * 60,  # 连接可以被重复利用多久（单位是秒），超时会重新创建，-1表示永久
            'TIMEOUT': 10,  # 池中没有连接最多等待时间
        }
    },
}

# redis配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        "LOCATION": 'redis://127.0.0.1:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # 'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                # "decode_responses": True,  # 自动转化字节为字符
            },
            # 'PASSWORD':'XXX'
        }
    },
    'offline_msgs': {
        'BACKEND': 'django_redis.cache.RedisCache',
        "LOCATION": 'redis://127.0.0.1:6379/6',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # 'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                # "decode_responses": True,  # 自动转化字节为字符
            },
            # 'PASSWORD':'XXX'
        }
    }
}

COS_SECRETID = 'AKIDc7QZWGp05ytdBWeZHm392h9QVQAj4GI8'
COS_SECRETKEY = 'gBWeaLtFPTO8f1A8tTnz0qT5XnqjQuCH'

PAGE_SIZE = 5

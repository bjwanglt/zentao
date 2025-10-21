from celery import Celery, signals
import os

# 1 导入配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zentao.settings')

# 2 创建celery实例
app = Celery('zentao_celery')
app.config_from_object('zentao.settings', namespace='CELERY')

# 3 调整 init 文件

# 4 其他地方引用 （装饰器将函数抓换为Task实例）
'''
from celery import shared_task

@shared_task
def XXX(...):
    pass
'''

# 5 自动去所有注册app中寻找 Task 并注册到celery实例中
app.autodiscover_tasks()

# 扩展： celery的信号机制  [这是回调的方式之一，针对的是全部的任务，也可以通过为任务绑定基类，这样可以个性化]


# 6 本地启动测试
'''
celery -A zentao worker -l info -P eventlet
celery -A zentao worker -l info -P solo
celery -A zentao worker -l info -P prefork

'''

import web.celery_handlers

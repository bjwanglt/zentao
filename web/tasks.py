import time

from celery import shared_task, Task, Celery
from django.core.mail import EmailMessage

import eventlet


class TaskWithCallback(Task):

    def on_success(self, retval, task_id, args, kwargs):
        pass

    def on_retry(self, reason_exc, req_id, req_args, req_kwargs, einfo):
        print(f'---------- TaskWithCallback  retry -------------')


from celery.app.task import Task


@shared_task(name="日报邮件", bind=True, autoretry_for=(Exception,), base=TaskWithCallback,
             retry_kwargs=dict(max_retries=3, countdown=5, ))
def send_report(self: Task, email_list, project_id):
    email = EmailMessage(
        subject='日报表',
        body=f'{project_id} 请查收图表',
        from_email='2597843280@qq.com',
        to=email_list
    )
    print('>>>>>>>>>>  发送成功 <<<<<<<<<<<<')

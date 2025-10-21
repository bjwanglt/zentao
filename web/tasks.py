from celery import shared_task
from django.core.mail import EmailMessage

from celery.app.task import Task


@shared_task(name="项目进度_日报邮件", bind=True, autoretry_for=(Exception,),
             retry_kwargs=dict(max_retries=3, countdown=5, ))
def send_report(self: Task, email_list, project_id):
    email = EmailMessage(
        subject='日报表',
        body=f'{project_id} 请查收图表',
        from_email='2597843280@qq.com',
        to=email_list
    )
    email.send()
    print(f'>>>>>>>>>>  发送成功 {email_list=}  {project_id=} <<<<<<<<<<<<')

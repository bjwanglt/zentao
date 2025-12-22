from celery import shared_task, group
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


'''
@shared_task(name='数据分片_index', bind=True, autoretry_for=(Exception,),
             retry_kwargs=dict(max_retries=3, countdown=5, ))
def data_sharding_index(self: Task):
    # 触发一个总的分片任务
    datas = list(range(1, 11))
    num = 5
    split_num = len(datas) // num
    subtasks = list()
    for i in range(num):
        subtasks.append(
            data_sharding_handler.s(
                datas[i * split_num: (i + 1) * split_num if i != num - 1 else None]
            )
        )
    task_group = group(*subtasks)
    task_group.delay()


@shared_task(name='数据分片_handler', bind=True, autoretry_for=(Exception,),
             retry_kwargs=dict(max_retries=3, countdown=5, ))
def data_sharding_handler(self: Task, datas: list):
    # 触发一个总的分片任务
    print(f'i get values: {datas}')
    print(self.app.tasks)
    if 10 in datas:
        1/0
'''

from celery.signals import task_postrun, task_retry


@task_postrun.connect
def set_periodic_name(sender=None, task_id=None, task=None, args=None, kwargs=None, **rest):
    from django_celery_results.models import TaskResult

    try:
        beat_info = getattr(task.request, 'headers', {}).get('django-celery-beat')
        if beat_info and 'periodic_task_name' in beat_info:
            TaskResult.objects.filter(task_id=task_id).update(
                periodic_task_name=beat_info['periodic_task_name']
            )
    except Exception as e:
        pass


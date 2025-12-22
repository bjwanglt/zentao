from django_celery_beat.schedulers import DatabaseScheduler
from celery.beat import _evaluate_entry_args, _evaluate_entry_kwargs


class CustomDatabaseScheduler(DatabaseScheduler):
    def apply_async(self, entry, producer=None, advance=True, **kwargs):
        # 先推进调度状态
        entry = self.reserve(entry) if advance else entry

        # 生成 args/kwargs
        entry_args = _evaluate_entry_args(entry.args)
        entry_kwargs = _evaluate_entry_kwargs(entry.kwargs)

        # 修改 headers: 将 periodic_task_name 改为 entry.id
        headers = entry.options.get('headers', {}).copy()
        headers['django-celery-beat'] = {
            'periodic_task_name': str(entry.model.id)  # entry.task_id 就是 PeriodicTask.id
        }
        entry.options['headers'] = headers

        # 调用原逻辑投递
        task = self.app.tasks.get(entry.task)
        if task:
            return task.apply_async(entry_args, entry_kwargs,
                                    producer=producer,
                                    **entry.options)
        else:
            return self.send_task(entry.task, entry_args, entry_kwargs,
                                  producer=producer,
                                  **entry.options)

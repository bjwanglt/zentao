from urllib.parse import urlencode

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpRequest
from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse
from utils.http_response import SysHttpResponse
from web.form.wiki_forms import wiki_form
from web import models
from django.views.decorators.csrf import csrf_exempt


def wiki(request: HttpRequest, pid):
    method = request.method
    if method == 'GET':
        wid: str = request.GET.get('wid', '')
        wiki_obj = None
        if wid and wid.isdigit():
            wiki_obj = models.Wiki.objects.filter(id=wid).first()
        return render(request, 'web/wiki/wiki.html', dict(wiki_obj=wiki_obj))


def add(request, pid):
    method = request.method
    if method == 'GET':
        form = wiki_form(request)
        return render(request, 'web/wiki/wiki_add.html', dict(form=form))
    if method == 'POST':
        form = wiki_form(request, data=request.POST)
        if not form.is_valid():
            return render(request, 'web/wiki/wiki_add.html', dict(form=form))
        instance = form.instance
        instance.project_id = request.proid
        if instance.parent_id:
            instance.depth = models.Wiki.objects.filter(id=instance.parent_id).values('depth').first().get('depth') + 1
        instance.save()
        # 重定向到文章预览界面
        reverse_url = reverse('web:wiki', kwargs=dict(pid=pid))
        query_param = urlencode(dict(wid=instance.id))
        return redirect(f'{reverse_url}?{query_param}')


def getcata(request, pid):
    # 返回目录信息
    res = SysHttpResponse()
    res.status = True
    wiki_cata = models.Wiki.objects.filter(project_id=pid).values('id', 'title', 'parent_id').order_by('depth')
    res.errors_or_data = list(wiki_cata)
    return JsonResponse(res.get_dict())


def delete(request, pid, wid):
    if pid and str(pid).isdigit() and wid and str(wid).isdigit():
        models.Wiki.objects.filter(project_id=pid, id=wid).delete()
    return redirect(reverse('web:wiki', kwargs={'pid': pid}))


def update(request: HttpRequest, pid, wid):
    method = request.method
    wiki_instance = models.Wiki.objects.filter(project_id=pid, id=wid).first()
    if method == 'GET':
        form = wiki_form(request, instance=wiki_instance)
        return render(request, 'web/wiki/wiki_add.html', dict(form=form))
    form = wiki_form(request, data=request.POST, instance=wiki_instance)
    if form.is_valid():
        instance = form.instance
        # 处理文章层级
        if instance.parent_id:
            instance.depth = models.Wiki.objects.filter(id=instance.parent_id).values('depth').first().get('depth') + 1
        instance.save()
        # 重定向到文章预览界面
        reverse_url = reverse('web:wiki', kwargs=dict(pid=pid))
        query_param = urlencode(dict(wid=wid))
        return redirect(f'{reverse_url}?{query_param}')


@csrf_exempt
def upload(request, pid):
    # https://store1-1257180138.cos.ap-beijing.myqcloud.com/IMG_3035.jpg
    try:
        file: InMemoryUploadedFile = request.FILES.get('editormd-image-file', None)
        query_folder = request.GET.get('folder')
        folder = query_folder if query_folder else 'wiki'
        if folder not in ('wiki','bug','file'):
            raise RuntimeError('参数传递错误')
        folder_path = (folder,)
        if file:
            file_name = file.name
            file_stream = file.file
            from utils.ope_cos import upload_file, get_file_url, DEFAULT_BUCKET
            pro = models.Project.objects.filter(id=pid).first()
            bucket_name = pro.bucket_name
            upload_file(bucket_name=bucket_name, file_stream=file_stream, file_name=file_name, folder_path=folder_path)
            return JsonResponse(
                dict(success=1, message='上传成功',
                     url=get_file_url(bucket_name=bucket_name, file_key=file_name, folder_path=''.join(folder_path)))
            )
    except Exception as e:
        return JsonResponse(
            dict(success=0, message=str(e), url='')
        )

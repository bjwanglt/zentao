from django.conf import settings
from django.core.paginator import Paginator, Page
from django.db import models
from django.conf import settings

from utils.http_response import SysHttpResponse


def get_pagination(queryset: models.QuerySet, page: int) -> SysHttpResponse:
    res = SysHttpResponse()
    try:
        pageobj = Paginator(queryset, settings.PAGE_SIZE)
        data: Page = pageobj.get_page(page)
        res.status = True
        res.errors_or_data = dict(
            datas=list(data),
            pagination=dict(
                current_page=data.number,
                page_size=int(settings.PAGE_SIZE),
                total_count=pageobj.count,
                total_pages=pageobj.num_pages,
                has_next=data.has_next(),
                has_previous=data.has_previous(),
                previous_page=data.previous_page_number() if data.has_previous() else None,
                next_page=data.next_page_number() if data.has_next() else None
            )
        )
    except Exception as e:
        res.status = False
        print(f'数据分页报错 {e}')
    finally:
        return res

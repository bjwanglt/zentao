from django.http import HttpRequest
from django.utils.safestring import mark_safe


class CheckFilterCondition:
    def __init__(self, request: HttpRequest, title: str, field: str, choices):
        """
        request: 请求实例
        title: 查询条件名称
        field: 字段名称
        choices: 查询条件范围
        """
        self.title = title
        self.choices = choices
        self.request = request
        self.field = field

    def __iter__(self):
        for c in self.choices:
            item_val = str(c[0])
            checked = ''
            # 当前请求参数
            query_dict = self.request.GET.copy()
            query_dict._mutable = True  # <QueryDict: {'page': ['2'], 'status': ['1']}>
            if 'page' in query_dict:
                query_dict.pop('page')
            query_vals = query_dict.getlist(self.field)
            if item_val in query_vals:
                checked = 'checked'
            # 生成下次点击的请求URL
            if item_val in query_dict.getlist(self.field):
                query_vals.remove(item_val)
            else:
                query_vals.append(item_val)
            query_dict.setlist(self.field, query_vals)
            href_url = '?' + query_dict.urlencode()
            yield mark_safe(
                f'<a class="cell" href="{href_url}"><input type="checkbox" {checked} {item_val} /><label>{c[1]}</label></a>')


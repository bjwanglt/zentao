from django import forms


class BootstrapMixin:
    """
    为forms.Form字段自动绑定form-control样式，以及placeholder
    """
    # 不需要添加bootstrap的字段名称
    exclude_filed_name = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  #
        for field_name, field in self.fields.items():
            if field_name in self.exclude_filed_name:
                continue
            class_val = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (class_val + ' form-control').strip()
            if 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = '请输入' + (field.label or '')

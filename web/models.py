from django.db import models


class UserInfo(models.Model):
    username = models.CharField(verbose_name='用户', max_length=32)
    email = models.EmailField(verbose_name='邮箱', max_length=32)
    phone = models.CharField(verbose_name='手机', max_length=32)
    password = models.CharField(verbose_name='密码', max_length=32)
    price_policy_id = models.IntegerField(verbose_name='价格策略')

    def __str__(self):
        return self.username

    class Meta:
        managed = False
        db_table = 'user_info'


class PricePolicy(models.Model):
    """价格策略"""
    catagory_choices = (
        (1, '免费版'),
        (2, '收费版'),
        (1, '其他版'),
    )

    category = models.SmallIntegerField(verbose_name='收费类型', default=1, choices=catagory_choices)
    title = models.CharField(verbose_name='标题', max_length=32)
    price = models.DecimalField(verbose_name='价格', max_digits=10, decimal_places=2)
    project_num = models.PositiveIntegerField(verbose_name='项目数')
    project_member = models.PositiveIntegerField(verbose_name='项目成员数')
    project_space = models.PositiveIntegerField(verbose_name='单项目空间')
    per_file_size = models.PositiveIntegerField(verbose_name='单文件大小（M）')
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        db_table = 'price_policy'
        managed = False


class Transaction(models.Model):
    """交易记录"""
    status_choice = (
        (1, '未支付'), (2, '已支付')
    )

    status = models.SmallIntegerField(verbose_name='状态', choices=status_choice)
    order = models.CharField(verbose_name='订单号', max_length=50, unique=True)
    user_id = models.IntegerField(verbose_name='用户ID')
    user_name = models.CharField(verbose_name='用户姓名', max_length=20)
    price_policy_id = models.IntegerField(verbose_name='价格策略ID')
    count = models.IntegerField(verbose_name='数量（年）', help_text='-1表示无限量', default=0)
    price = models.DecimalField(verbose_name='实际支付价格', max_digits=10, decimal_places=2)
    start_time = models.DateTimeField(verbose_name='开始时间', null=True, blank=True)
    end_time = models.DateTimeField(verbose_name='结束时间', null=True, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        db_table = 'transaction'


class Project(models.Model):
    """项目"""
    COLOR_CHOICES = (
        (1, '#56b8eb'),
        (2, '#f28033'),
        (3, '#ebc656'),
        (4, '#a2d148'),
        (5, '#20BFA4'),
        (6, '#7461c2'),
        (7, '#BE8C3EFF'),
    )

    name = models.CharField(verbose_name='项目名称', max_length=32)
    color = models.SmallIntegerField(verbose_name='颜色', choices=COLOR_CHOICES, default=1)
    desc = models.CharField(verbose_name='项目描述', max_length=255, null=True, blank=True)
    use_space = models.PositiveIntegerField(verbose_name='项目已用空间', default=0)
    # star = models.BooleanField(verbose_name='是否星标', default=False)
    join_count = models.SmallIntegerField(verbose_name='参与人数', default=1)
    create_id = models.IntegerField(verbose_name='创建人ID')
    create_name = models.CharField(verbose_name='创建人姓名', max_length=32)
    update_id = models.IntegerField(verbose_name='修改人ID')
    update_name = models.CharField(verbose_name='修改人姓名', max_length=32)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='修改时间', auto_now=True)
    bucket_name = models.CharField(verbose_name='桶', max_length=64, null=True, blank=True)

    class Meta:
        db_table = 'project'


class ProjectUser(models.Model):
    """项目参与者"""
    USER_ROLE = ((1, '创建人'), (2, '参与人'))
    project_id = models.IntegerField(verbose_name='项目ID')
    project_name = models.CharField(verbose_name='项目名称', max_length=64)
    user_id = models.IntegerField(verbose_name='用户ID')
    user_name = models.CharField(verbose_name='用户姓名', max_length=32)
    user_role = models.SmallIntegerField(verbose_name='角色', choices=USER_ROLE)
    star = models.BooleanField(verbose_name='是否星标', default=False)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        db_table = 'project_user'


class Wiki(models.Model):
    """wiki"""
    title = models.CharField(verbose_name='标题', max_length=100)
    content = models.TextField(verbose_name='内容')
    project_id = models.IntegerField(verbose_name='项目ID')
    parent_id = models.IntegerField(verbose_name='父级ID', null=True, blank=True)
    depth = models.SmallIntegerField(verbose_name='层级', default=1)

    class Meta:
        db_table = 'wiki'


class ProFile(models.Model):
    TYPE_CHOICES = (
        (1, '文件夹'),
        (2, '文件'),
    )

    project_id = models.IntegerField(verbose_name='项目ID')
    file_name = models.CharField(verbose_name='名称', max_length=64)
    file_type = models.SmallIntegerField(verbose_name='类型', choices=TYPE_CHOICES)
    parent_id = models.IntegerField(verbose_name='父级ID', null=True, blank=True)
    bucket_name = models.CharField(verbose_name='桶', max_length=64)
    file_path = models.CharField(verbose_name='文件地址', max_length=200, null=True, blank=True)
    file_size = models.PositiveIntegerField(verbose_name='文件大小')
    create_id = models.IntegerField(verbose_name='创建人ID', null=True)
    create_name = models.CharField(verbose_name='创建人姓名', max_length=32, null=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, null=True)
    update_id = models.IntegerField(verbose_name='修改人ID', null=True)
    update_name = models.CharField(verbose_name='修改人姓名', max_length=32, null=True)
    update_time = models.DateTimeField(verbose_name='修改时间', auto_now=True, null=True)
    key = models.CharField(verbose_name='cos唯一标识', null=True, max_length=100, unique=True)

    @property
    def file_size_display(self):
        return round(self.file_size / 1024 / 1024, 2)

    class Meta:
        db_table = 'pro_file'


class Issues(models.Model):
    """ 问题 """
    priority_choices = (
        ("danger", "高"),
        ("warning", "中"),
        ("success", "低"),
    )
    status_choices = (
        (1, '新建'),
        (2, '处理中'),
        (3, '已解决'),
        (4, '已忽略'),
        (5, '待反馈'),
        (6, '已关闭'),
        (7, '重新打开'),
    )
    mode_choices = (
        (1, '公开模式'),
        (2, '隐私模式'),
    )
    project = models.ForeignKey(verbose_name='项目', to='Project', db_constraint=False, on_delete=models.DO_NOTHING)
    issues_type = models.ForeignKey(verbose_name='问题类型', to='IssuesType', on_delete=models.DO_NOTHING,
                                    db_constraint=False, null=True, blank=True)
    module = models.ForeignKey(verbose_name='模块', to='Module', null=True, blank=True, db_constraint=False,
                               on_delete=models.DO_NOTHING)
    subject = models.CharField(verbose_name='主题', max_length=80)
    desc = models.TextField(verbose_name='问题描述')
    priority = models.CharField(verbose_name='优先级', max_length=12, choices=priority_choices, default='danger')
    status = models.SmallIntegerField(verbose_name='状态', choices=status_choices, default=1)
    assign = models.ForeignKey(verbose_name='指派', to='UserInfo', related_name='task', null=True, blank=True,
                               db_constraint=False, on_delete=models.DO_NOTHING)
    attention = models.ManyToManyField(verbose_name='关注者', to='UserInfo', related_name='observe', blank=True,
                                       through='IssueAttention')
    start_date = models.DateField(verbose_name='开始时间', null=True, blank=True)
    end_date = models.DateField(verbose_name='结束时间', null=True, blank=True)
    mode = models.SmallIntegerField(verbose_name='模式', choices=mode_choices, default=1)
    parent = models.ForeignKey(verbose_name='关联问题', to='self', related_name='child', null=True, blank=True,
                               on_delete=models.SET_NULL)
    creator = models.ForeignKey(verbose_name='创建者', to='UserInfo', related_name='create_problems',
                                db_constraint=False, on_delete=models.DO_NOTHING)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    latest_update_datetime = models.DateTimeField(verbose_name='最后更新时间', auto_now=True)

    def __str__(self):
        return self.subject

    class Meta:
        db_table = 'issue_info'


class IssueAttention(models.Model):
    """ 问题的关注者信息 """
    issue = models.ForeignKey(Issues, verbose_name='问题', db_constraint=False, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(UserInfo, verbose_name='关注者', db_constraint=False, on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'issus_attention_info'


class Module(models.Model):
    """ 模块（里程碑）"""
    project = models.ForeignKey(verbose_name='项目', to='Project', db_constraint=False, on_delete=models.DO_NOTHING)
    title = models.CharField(verbose_name='模块名称', max_length=32)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'module_info'


class IssuesType(models.Model):
    """ 问题类型 例如：任务、功能、Bug """
    title = models.CharField(verbose_name='类型名称', max_length=32)
    project = models.ForeignKey(verbose_name='项目', to='Project', db_constraint=False, on_delete=models.DO_NOTHING)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'issue_type'


class IssuesReply(models.Model):
    """ 问题评论 """
    reply_type_choices = (
        (1, '修改记录'),
        (2, '评论')
    )
    reply_type = models.IntegerField(verbose_name='类型', choices=reply_type_choices, default=2)
    issues = models.ForeignKey(verbose_name='问题', to=Issues, db_constraint=False, on_delete=models.DO_NOTHING)
    content = models.TextField(verbose_name='评论内容')
    creater = models.ForeignKey(verbose_name='创建者', to=UserInfo, related_name='create_reply', db_constraint=False,
                                on_delete=models.DO_NOTHING)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    parent = models.ForeignKey(verbose_name='父级评论', to='self', null=True, blank=True, on_delete=models.DO_NOTHING,
                               related_name='child_replay')
    root = models.SmallIntegerField(verbose_name='评论层级', default=0)
    child_num = models.SmallIntegerField(verbose_name='子评论数量', default=0)

    class Meta:
        db_table = 'issue_replay'


'''
class ProjectInvite(models.Model):
    """ 项目邀请码 """
    period_choices = (
        (30, '30分钟'),
        (60, '1小时'),
        (300, '5小时'),
        (1440, '24小时'),
    )
    project = models.ForeignKey(verbose_name='项目', to='Project',db_constraint=False, on_delete=models.DO_NOTHING)
    code = models.CharField(verbose_name='邀请码', max_length=64, unique=True)
    count = models.PositiveIntegerField(verbose_name='限制数量', null=True, blank=True, help_text='空表示无数量限制')
    use_count = models.PositiveIntegerField(verbose_name='已邀请数量', default=0)
    period = models.IntegerField(verbose_name='有效期', choices=period_choices, default=1440)
    create_datetime = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    creator = models.ForeignKey(verbose_name='创建者', to='UserInfo', related_name='create_invite')
'''

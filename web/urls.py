from django.urls import path, include, re_path
from web.views import account, promanage, prowiki, profile, issue, overview, statistics

urlpatterns = [
    # 用户登录相关
    path('register/', account.register, name='register'),
    path('login/', account.login, name='login'),
    path('logout/', account.logout, name='logout'),
    path('get_checkcode/', account.get_checkcode, name='get_checkcode'),
    path('send/sms/', account.send_sms, name='send_sms'),
    path('index/', account.index, name='index'),

    # 用户管理中心页面跳转
    path('manage_index/', promanage.manage_index, name='manage_index'),
    # 用户管理中心项目查询
    path('manage_pro/', promanage.manage_pro, name='manage_pro'),

    re_path(r'^manage/(?P<pid>\d+)/', include([
        re_path(r'^(?P<startype>[01])/star/$', promanage.star, name='star'),
        path('view/', promanage.view, name='view'),
        # wiki模块
        path('wiki/', prowiki.wiki, name='wiki'),
        path('wiki/add', prowiki.add, name='wiki_add'),
        path('wiki/upload/', prowiki.upload, name='wiki_upload'),
        path('wiki/delete/<int:wid>/', prowiki.delete, name='wiki_delete'),
        path('wiki/update/<int:wid>/', prowiki.update, name='wiki_update'),
        path('wiki/getcata', prowiki.getcata, name='getcata'),
        # 文件模块
        path('file/', profile.file, name='file'),
        path('file/upload/', profile.upload, name='file_upload'),
        path('file/delete/', profile.delete, name='file_delete'),
        path('file/delete/folder', profile.delete_folder, name='file_delete_folder'),
        path('file/get_temp_sign/', profile.get_temp_sign, name='get_temp_sign'),
        # 问题模块
        path('issue/', issue.issue, name='issue'),
        path('issue/detail/<int:issue_id>/', issue.issue_detail, name='issue_detail'),
        path('issue/edit/<int:issue_id>/', issue.issue_edit, name='issue_edit'),
        path('issue/replay/<int:issue_id>/', issue.issue_replay, name='issue_replay'),
        # 邀请成员相关
        path('get_invite_url/', issue.get_invite_url, name='get_invite_url'),
        # 概览
        path('overview/', overview.over_view, name='overview'),
        path('statistics/', statistics.statistics, name='statistics')
    ])),

    path('invite/', issue.invite, name='invite')

]

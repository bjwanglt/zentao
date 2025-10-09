from django.dispatch.dispatcher import Signal

# 自定义信号量
user_register_sl = Signal(
    providing_args=(
        # 用户ID
        'user_id'
    )
)

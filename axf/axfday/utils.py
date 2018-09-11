import uuid
import hashlib
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.template import loader
from functools import wraps

from .models import AxfUser


def create_random_str():
    uuid_val = uuid.uuid4()
    uuid_str = str(uuid_val).encode("utf-8")
    md5 = hashlib.md5()
    md5.update(uuid_str)
    return md5.hexdigest()

def send_confirm_email(user, host):
    # 拼接验证连接
    random_str = create_random_str()

    url = "http://{host}/axf/confirm/{random_str}".format(
        host=host,
        random_str=random_str
    )
    # 发送邮件
    temp = loader.get_template("user/user_confirm.html")
    # 渲染模板
    html = temp.render({"url": url})
    # 拼接邮件的发送内容
    title = "红浪漫"
    msg = ""
    email_from = settings.DEFAULT_FROM_EMAIL
    receives = [user.email]
    send_mail(
        title,
        msg,
        email_from,
        receives,
        fail_silently=False,
        html_message=html
    )
    # 设置缓存
    cache.set(random_str, user.id, settings.CACHE_AGE)
    return True

NOT_LOGIN = 2

def check_login(func):

    @wraps(func)
    def inner(req, *args, **kwargs):
        user = req.user
        if isinstance(user, AxfUser):
            return func(req, *args, **kwargs)
        else:
            data = {"code": NOT_LOGIN,
                    "msg":"未登录",
                    "data": "/axf/login"
                    }
            return JsonResponse(data)
    return inner

def get_cart_money(cart_items):
    sum = 0
    for i in cart_items.filter(is_select=True):
        sum += i.goods.price * i.num

    return round(sum, 2)
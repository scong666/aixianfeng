from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views.generic import View

from .models import *
from .utils import send_confirm_email, check_login, get_cart_money

SUCCESS = 1
INVENTORY = 3


def home(req):
    # 读取轮播数据
    wheels = MyWheel.objects.all()
    navs = MyNav.objects.all()
    # 必购的数据
    musts = MustBuy.objects.all()
    shops = Shop.objects.all()
    data = {
        "title": "首页",
        "wheels": wheels,
        "navs": navs,
        "musts": musts,
        "shop0": shops[0],
        "shop1_3": shops[1:3],
        "shop3_7": shops[3:7],
        "shop_last": shops[7:],
        "mains": MainShow.objects.all()
    }
    return render(req, 'home/home.html', data)


@login_required(login_url="/axf/login")
def cart(req):
    user = req.user
    # 拿到用户对应的购物车数据
    cart_items = Cart.objects.filter(user=user)
    is_select_all = True
    # 看没被选中的数据 有没有
    if Cart.objects.filter(user=user, is_select=False).exists():
        is_select_all = False
    #     算钱
    # sum = 0
    # for i in cart_items.filter(is_select=True):
    #     sum += i.goods.price * i.num

    data = {
        "title": "购物车",
        "cart_items": cart_items,
        "uname": user.username,
        "phone": user.phone,
        "address": user.address,
        "is_select_all": is_select_all,
        "sum_money": get_cart_money(cart_items)
    }
    return render(req, 'cart/cart.html', data)


def market(req):
    return redirect(reverse("axf:market_with_params", args=(104749, 0, 1)))


def market_with_params(req, typeid, sub_type_id, sort_type):
    """
        1 综合排序
        2 销量
        3 价格
    :param req:
    :param typeid:
    :param sub_type_id:
    :return:
    """
    sub_type_id = int(sub_type_id)
    # 拿到所有的分类数据
    my_types = GoodsTypes.objects.all()
    # 通过typeid拿商品数据
    my_goods = Goods.objects.filter(
        categoryid=int(typeid)
    )
    # 拿一级分类数据
    current_type = my_types.filter(typeid=typeid).first()
    # 拿二级分类数据
    # result = []
    # sub_types_str = current_type.childtypenames
    # sub_types_array = sub_types_str.split("#")
    # for i in sub_types_array:
    #     tmp = i.split(":")
    #     print(tmp)
    #     result.append(tmp)
    # print(result)
    result = [i.split(":") for i in current_type.childtypenames.split("#")]

    # 通过二级分类数据过滤商品
    result_goods = None
    if sub_type_id == 0:
        result_goods = my_goods
    else:
        result_goods = my_goods.filter(childcid=sub_type_id)
    # 确定数据集以后 做排序

    if sort_type == "2":
        result_goods = result_goods.order_by("productnum")
    elif sort_type == "3":
        result_goods = result_goods.order_by("price")
    else:
        pass

    # 商品数据确定了，继续去看对应用户购物车的商品对应的数量
    user = req.user
    if isinstance(user, AxfUser):
    #     查用户的购物车数据
        cart_items = Cart.objects.filter(user=user).values("goods_id", "num")
        # print(cart_items)
        tmp_dict = {}
        for i in cart_items:
            tmp_dict[i.get("goods_id")] = i.get("num")
        # print(tmp_dict)
        for g in result_goods:
            if g.id in tmp_dict:
                # 如果存在在购物车 那修改当前商品数量
                g.current_num = tmp_dict.get(g.id)
    else:
        pass
    data = {
        "title": "闪购",
        "types": my_types,
        "select_type_id": typeid,
        "goods": result_goods,
        "sub_types": result,
        "select_sub_type_id": str(sub_type_id),
        "sort_type": int(sort_type)
    }
    return render(req, 'market/market.html', data)


def mine(req):
    user = req.user
    is_login = False
    username = ""
    u_icon = ""
    if isinstance(user, AxfUser):
        is_login = True
        username = user.username
        if user.icon:
            u_icon = "http://" + req.get_host() + "/static/uploads/" +user.icon.url
        data = {
            "title": "我的",
            'is_login': is_login,
            'u_name': username,
            'icon': u_icon
        }
        return render(req, 'mine/mine.html', data)
    else:
        data = {
            "title": "我的",
            'is_login': is_login,
            'u_name': username,
            'icon': u_icon
        }
        return render(req, 'mine/mine.html', data)


class RegisterAPI(View):

    def get(self, req):
        return render(req, 'user/register.html')

    def post(self, req):
        params = req.POST
        icon_file = req.FILES.get("icon")
        uname = params.get("uname")
        pwd = params.get("pwd")
        c_pwd = params.get("c_pwd")
        email = params.get("email")

#         开始校验数据
        if uname and len(uname) >= 3:
#             继续校验此用户名是否可用
            if AxfUser.objects.filter(username=uname).exists():
#                 如果查到了数据说明用户名不可用
                return HttpResponse("用户不可用")
            else:
                if pwd and len(pwd)>0 and pwd == c_pwd:
#                     创建用户，发送验证邮件
                    user = AxfUser.objects.create_user(
                        username=uname,
                        password=pwd,
                        email=email,
                        is_active=False,
                        icon=icon_file
                    )
#                     发送验证邮件 需要的参数用户
                    if send_confirm_email(user, req.get_host()):
                        return HttpResponse("恭喜您注册成功")
                    else:
                        return HttpResponse("验证邮件发送失败")
                else:
                    return HttpResponse("好好学习，没事别抓人接口")
        else:
            return HttpResponse("好好学习，没事别抓人接口")


class LoginAPI(View):

    def get(self, req):
        return render(req, 'user/login.html')

    def post(self, req):
        params = req.POST
        uname = params.get("uname")
        pwd = params.get("pwd")
#         校验数据
        if uname and pwd and len(uname)>=3 and len(pwd)>0:
            # 校验用户
            user = authenticate(username=uname, password=pwd)
            if user:
                login(req, user)
                return redirect(reverse("axf:mine"))
            else:
                return redirect(reverse("axf:login"))
        else:
            return HttpResponse("别瞎搞")


def confirm(req, random_str):
    # 去那缓存拿数据
    uid = cache.get(random_str)

    if uid:
        # 通过uid找到用户,更新字段
        AxfUser.objects.filter(pk=int(uid)).update(
            is_active=True
        )
        return redirect(reverse("axf:login"))
    else:
        return HttpResponse("验证链接无效")


def logout_api(req):
    logout(req)
    return redirect(reverse("axf:mine"))

@check_login
def cart_api(req):
    user = req.user
    op_type = req.POST.get("op_type")
    g_id = int(req.POST.get("g_id"))

    #         通过商品id拿到商品数据
    goods = Goods.objects.get(pk=g_id)

    # 拿购物车数据
    cart_item = Cart.objects.filter(
        user_id=user.id,
        goods_id=goods.id
    )
    #         判断操作
    if op_type == "add":
        # 判断库存
        if goods.storenums < 1:
            data = {
                "code": INVENTORY,
                "msg": "您购买的商品暂无库存",
                "data": None
            }
            return JsonResponse(data)
        # 判断是不是第一次加
        # cart_item = Cart.objects.filter(
        #     user_id=user.id,
        #     goods_id=goods.id
        # )
        goods_num = 1
        if cart_item.exists():
            # 不是第一次添加
            cart = cart_item.first()
            cart.num += 1
            cart.save()
            goods_num = cart.num
        else:
            # 是第一次添加
            Cart.objects.create(
                user_id=user.id,
                goods_id=goods.id
            )
        data = {
            "code": SUCCESS,
            "msg": "ok",
            "data": goods_num
        }
        return JsonResponse(data)

    else:
        cart_data = cart_item.first()
        # 将数量减一
        cart_data.num -= 1
        # m默认数量是0
        goods_num = 0
        if cart_data.num == 0:
            cart_data.delete()
        else:
            cart_data.save()
            goods_num = cart_data.num
        data = {
            "code": SUCCESS,
            "msg":"ok",
            "data": goods_num
        }
        return JsonResponse(data)


def cart_status_api(req):
    params = QueryDict(req.body)
    user = req.user
    cart_item = Cart.objects.get(pk=int(params.get("c_id")))
    # 将选中状态置反
    cart_item.is_select = not cart_item.is_select
    cart_item.save()

    # 算钱
    cart_items = Cart.objects.filter(
        user=user,
        is_select=True
    )
    sum_money = get_cart_money(cart_items)

    # 判断全按钮状态
    is_select_all = True
    if Cart.objects.filter(user=user, is_select=False).exists():
        is_select_all = False
    #     返回结果
    data = {
        "code": SUCCESS,
        "msg": "ok",
        "sum_money": sum_money,
        "is_select_all": is_select_all,
        "current_item_status": cart_item.is_select
    }
    return JsonResponse(data)


def select_all_api(req):
    user = req.user
    # 查询到所有的用户对应的购物车数据
    cart_items = Cart.objects.filter(
        user=user
    )
    is_all_select, sum_money = True, 0
    # 判断是否存在 未选中的商品
    if cart_items.filter(is_select=False).exists():
        # 全选操作
        cart_items.filter(is_select=False).update(is_select=True)
        # is_all_select = True
        sum_money = get_cart_money(cart_items)
    else:
        cart_items.update(
            is_select=False
        )
        is_all_select = False
        # sum_money = 0
    #返回结果
    data = {
        "code":SUCCESS,
        "msg":'ok',
        'data': {
            "is_select_all": is_all_select,
            "sum_money": sum_money
        }
    }
    return JsonResponse(data)


def cartitem_api(req):
    user = req.user
    params = req.POST
    c_id = int(params.get("c_id"))
    op_type = params.get("op_type")
    # 先cid对应的数据
    cart_data = Cart.objects.get(pk=c_id)
    sum_money = item_num = 0
    is_select_all = True
    if op_type=="sub":
        # 减商品数量
        cart_data.num -= 1
        if cart_data.num == 0:
            cart_data.delete()
        #     要看全选按钮的状态
            if Cart.objects.filter(user=user,is_select=False).exists():
                is_select_all = False
            else:
                is_select_all = True
        else:
            cart_data.save()

            # 算钱 和 记录商品数量

            item_num = cart_data.num
            # 需要拿到所有该用户的选中商品的数据集
        cart_items = Cart.objects.filter(
            user=user,
            is_select=True
        )
        sum_money = get_cart_money(cart_items)
        data = {
            "code": SUCCESS,
            "msg": "ok",
            "data": {
                "sum_money": sum_money,
                "item_num": item_num,
                "is_select_all": is_select_all
            }
        }
        return JsonResponse(data)
    else:
        # 查库存
        if cart_data.goods.storenums < 1:
            data = {
                "code": INVENTORY,
                "msg": "库存不足",
                "data":None
            }
            return JsonResponse(data)
        # 加操作
        cart_data.num += 1
        cart_data.save()
        cart_items = Cart.objects.filter(
            user=user,
            is_select=True
        )
        sum_money = get_cart_money(cart_items)
        # 保存 返回数据
        data = {
            "code": SUCCESS,
            "msg": "ok",
            "data": {
                "sum_money": sum_money,
                "item_num": cart_data.num,

            }
        }
        return JsonResponse(data)


def order_api(req):
    user = req.user
    # 找购物车内被用户选中的数据
    cart_items = Cart.objects.filter(
        user=user,
        is_select=True
    )
    if not cart_items.exists():
        return JsonResponse({"code": 4, "msg": "无商品可下单"})

    # 创建订单
    order = Order.objects.create(
        user=user
    )
    # 创建订单详情
    for i in cart_items:
        OrderItem.objects.create(
            order=order,
            goods_id=i.goods_id,
            num=i.num
        )
    # 算钱
    sum_money = get_cart_money(cart_items)
    # 清空购物车选中的商品
    cart_items.delete()
    return render(req, "order/order.html", {"order":order, "money": sum_money})
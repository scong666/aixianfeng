$(function () {
    $("form").submit(function () {
        var uname = $("#name_id").val();
        var pwd = $("#pwd_id").val();
        var c_pwd = $("#c_pwd_id").val();

        if (uname.length <3) {
            alert("用户名过短");
            return false;
        }

    //    判断密码长度
        if (pwd.length<3) {
            alert("密码过短");
            return false;
        }
    //    判断密码个确认密码
        if (pwd != c_pwd){
            alert("两次密码输入不一致");
            return false;
        }
    //    通过以上校验 我们加密密码和确认密码
        var pwd_md5 = md5(pwd);
        var c_pwd_md5 = md5(c_pwd);

    //    将加密的值设置回去
        $("#pwd_id").val(pwd_md5);
        $("#c_pwd_id").val(c_pwd_md5);


    });
})
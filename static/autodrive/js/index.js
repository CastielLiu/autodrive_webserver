// 匿名函数利用括号包括,将自动自动执行
(function(){
//    var core_ws;
//    var core_ws_login = 0;

    var index = window.index = {
        test_key1: null,
        test_key2: null,
        core_ws: null,
        core_ws_login: 0,

        init: function(){
            // 保存当前对象指针, 便于子函数访问父对象
            var _this = this;

            // requestOnlineCars("测试组"); //http
            this.initEvent(); //初始化事件过滤器
        },

        initEvent: function(){
            var _this = this;
//            <div class="parent_class">
//                <div class="child_class" data-id="10" data-name="john"/>
//            </div>
//             //为类添加点击事件
//            $(document).on('click', '.parent_class .child_class', function(e){
//                var id = $(this).data('id'); // 获取类属性
//                var name = $(this).data('name'); // 获取类属性
//            })

            $(document).ready(function(e){
                _this.connect_core_ws();
            });

              // 方法无效，不知何故
//            $('.dashboard').on('load', function(){
//                connect_core_ws();
//            });

            // .class  #id
            $(document).on('click', '#getPathListBtn', function(e){
               requestPathList("测试组");
            });

            $(document).on('click', '#getPathBtn', function(e){
               requestPath(parseInt($('#pathid').val()));
            });

            $(document).on('click', '#wsTestBtn', function(e){
                ws = new WebSocket('ws://' + window.location.host + '/ws/autodrive/test/');
                ws.onopen = function(){
                    data = {"message": "test message"};
                    console.log(data);
                    ws.send(JSON.stringify(data));
                }

                ws.onmessage = function(msg){
                    console.log("msg");
                }

                ws.onclose = function(){

                }
            });




            $(document).on('click', '#flush_online_cars', function(e){
               requestOnlineCars("测试组"); //http
            });

            // 显示所有车辆位置  $(document)可以绑定动态页面事件
            $(document).on('click', '#showAllCarsPos', function(){
                var flag = $("#showAllCarsPos").prop("checked");
                $(".showCarPos").each(function () {
                    $(this).prop("checked", flag);
                });
            });
            $(document).on('click', '.showCarPos', function(){
                var flag = $(this).prop("checked");
                if (!flag) {
                    $("#showAllCarsPos").prop("checked", flag);
                }else{
                    if ($(".showCarPos").length == $(".showCarPos:checked").length) {
                        $("#showAllCarsPos").prop("checked", flag);
                    }
                }
            });
        },

        core_ws_onopen: function(){
//            tools.showMsgToast("websocket cnnected.", 3000);
            var userid = tools.getCookie('userid');
            var token = tools.getCookie('token');
            //        send_log("document.cookie: "+document.cookie);
            //        send_log("token: " + token);
            var data;
            if(typeof(token) == 'undefined' || typeof(userid) == 'undefined'){
                loginInfo.innerHTML = "用户名或token不存在, 请勿禁用cookie";
                return;
            }

            data = JSON.stringify({"type": "req_login", "data": {"userid": userid, "token": token}});

            tools.send_log(data);
            core_ws.send(data)
        },

        core_ws_onclose: function(evt){
            if(this.core_ws_login)
            {
                connectBtn.name = "connect";
                connectBtn.innerHTML = "连接";
                this.core_ws_login = 0;
                loginInfo.innerHTML = "";
            }
        },

        core_ws_onmessage: function(evt){
            var data, type, msg;
            try{ //json解析 异常捕获
                data = JSON.parse(evt.data);
                type = data.type;
                msg = data.msg;
                if(typeof(type) == "undefined")
                    return;
            }catch(err){
                return;
            }

            tools.receive_log("ws:" + JSON.stringify(data))

            // 登录反馈
            if(this.core_ws_login==0 && type=="res_login"){
                if(msg.result){ // 登录成功
                    this.core_ws_login = 1;
                    connectBtn.name = "disconnect";
                    connectBtn.innerHTML = "断开";
                    loginInfo.innerHTML = "登录成功";
                    return;
                }
                else
                    loginInfo.innerHTML = "帐号或密码错误";
            }
            else if(type == "rep_car_state"){
              // 状态数据
              // info.id
              // info.car_state
            }
            else if(type == "res_online_car"){
//                console.log(msg.cars)
                showOnlineCars(msg.cars)
            }
        },

        connect_core_ws: function(){
            core_ws = new WebSocket('ws://' + window.location.host + '/ws/autodrive/web/core/');
            core_ws.onopen = this.core_ws_onopen;
            core_ws.onmessage = this.core_ws_onmessage;
            core_ws.onclose = this.core_ws_onclose;
        },

    };

    index.init();
})();


function showOnlineCars(cars){
    console.log(cars);
    var tab="<table border='1'>";
    tab+="<tr><th>车辆ID</th><th>车辆名称</th><th>" +"<input type='checkbox' " + "id='showAllCarsPos'>显示位置"+"</th>"
        +"<th>是否在线</th>"+"<th>分组</th>"
        +"</tr>";

    for(var i in cars){
        tab += "<tr><td>" + cars[i].id + "</td><td>" + cars[i].name + "</td><td>"
            +"<input type='checkbox' " +"class='showCarPos' name='" + cars[i].id + "'/>显示位置"+"</td>"
            +"<td>" + (cars[i].online?"在线":"离线") + "</td><td>" +cars[i].group + "</td>"
            +"</tr>"
    }
    tab+="</table>";
    console.log(tab);

    var divv=document.getElementById("cars_list");
    divv.innerHTML=tab;
}
// 匿名函数利用括号包括,将自动自动执行
(function(){
    //所有JS全局对象,函数以及变量均自动成为window对象的成员
    //为避免全局变量冲突, 将当前js文件中的功能封装到匿名函数
    //为便于外部进行访问, 手动将index设置为window的成员
    var index = window.index = {
        test_key1: null,
        test_key2: null,
        core_ws: null,
        core_ws_login: 0,
        core_ws_initiative_close: 0,  //主动关闭(收到被迫下线信息/xx)
        update_cars_clock: null,

        user_groupname: $('#active_usergroup').html(),
        user_groupid: tools.getCookie('groupid'),
        user_id: tools.getCookie('userid'),

        init: function(){
            // 保存当前对象指针, 便于子函数访问父对象
            var _this = this;

            // requestOnlineCars("测试组"); //http
            this.initEvent(); //初始化事件过滤器
            requestOnlineCars("");
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

            // .class  #id
            $(document).on('click', '#getPathListBtn', function(e){
               requestPathList(_this.user_groupid);
            });

            $(document).on('click', '#getPathBtn', function(e){
                var pathid = $("#pathList option:selected").val();
                requestPathTraj(parseInt(pathid));
            });

            $(document).on('click', '#connectBtn', function(e){
                if(_this.core_ws_login)
                    _this.core_ws.close();
                else
                    _this.connect_core_ws();
            });

            $(document).on('click', '#logoutBtn', function(e){
               _this.ws_logout();
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
            $(document).on('click', '#wsSendBtn', function(e){
                var msg = JSON.stringify({"type": "test", "data": {"ping": $('#ws_test_data').val()}});
                console.log(msg);
               _this.core_ws.send(msg);
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

                window.clearInterval(_this.update_cars_clock);
                if($(".showCarPos:checked").length > 0){
                    _this.update_cars_clock = setInterval(requestCarsPosition, 1000);
                }
            });
            // 显示某车辆位置
            $(document).on('click', '.showCarPos', function(){
                //处理全选与全不选事件逻辑
                var flag = $(this).prop("checked");
                if (!flag) {
                    $("#showAllCarsPos").prop("checked", flag);
                }else{
                    if ($(".showCarPos").length == $(".showCarPos:checked").length) {
                        $("#showAllCarsPos").prop("checked", flag);
                    }
                }
                // 先关闭定时器,再按需打开
                window.clearInterval(_this.update_cars_clock);
                if($(".showCarPos:checked").length > 0){
                    _this.update_cars_clock = setInterval(requestCarsPosition, 1000);
                }
                console.log($(this).name);
            });
            //车辆ID点击事件
            $(document).on('click', '.doTask', function(){
//                console.log($(this).html());
                $('#task-msgBox').css('display', 'block');
                $('#taskCarId').val($(this).html());
                $("#msgBoxInfomation").html("");
                requestPathList(_this.user_groupid); //请求路径列表
            });
            //关闭消息对话框
            $(document).on('click', '#closeMsgBox', function(){
                $('#task-msgBox').css('display', 'none');
            });
            //终止车辆当前任务
            $(document).on('click', '#stopCurrentTask', function(){
                //stopCurrentTask()
            });
            //启动新任务
            $(document).on('click', '#startNewTask', function(){
                var object = $(this);
                object.siblings().hide();
                object.attr('disabled',true);
                var msgTextObj = $("#msgBoxInfomation");
                msgTextObj.html("正在启动新任务，请稍等...");
                var carid = $('#taskCarId').val();
                var targetPathid = $("#pathList option:selected").val();
                var targetSpeed = $("#taskTargetSpeedList option:selected").val();
                HttpRequest2({
                    cmd: {"type":"req_start_task", "data": {"car_id": carid, "path_id": targetPathid, "speed": targetSpeed}},
                    url: "",
                    timeout: 10000, //10s
                    async: true,  //async 为false时表示同步, 将导致html页面不更新
                    done: function(data){
                        console.log(data);
                        dict = JSON.parse(data);
                        type = dict.type;
                        code = dict.code;
                        msg = dict.msg;
                        console.log(data);
                        if(code === 0){
                            msgTextObj.html("任务启动成功！");//;
                        }
                        else{
                            msgTextObj.html("任务启动失败: "+msg);//;
                        }
                    },
                    complete: function(xhr, status){
                        object.attr('disabled', false);
                        object.siblings().show();
                        if(status == 'timeout')
                            msgTextObj.html("请求超时");
                    },
                });
            });
            //终止当前任务
            $(document).on('click', '#stopCurrentTask', function(){
                var _this = this;
                var object = $(this);
                var msgTextObj = $("#msgBoxInfomation");

                object.siblings().hide(); object.attr('disabled',true);

                $("#msgBoxInfomation").html("正在请求终止正在执行的任务，请稍等...");
                var carid = $('#taskCarId').val();
                HttpRequest2({
                    cmd: {"type":"req_stop_task", "data": {"car_id": carid}},
                    url: "",
                    timeout: 10000, //10s
                    async: true,  //async 为false时表示同步, 将导致html页面不更新
                    done: function(data){
                        dict = JSON.parse(data);
                        code = dict.code;
                        msg = dict.msg;
                        if(code === 0){
                            msgTextObj.html("当前任务已终止！");//;
                        }
                        else{
                            msgTextObj.html("当前任务终止失败: "+msg);//;
                        }
                    },
                    complete: function(xhr, status){
                        object.attr('disabled', false);
                        object.siblings().show();
                        if(status == 'timeout')
                            msgTextObj.html("请求超时");

                    },
                });
            });
        },

        ws_logout: function(){
            this.core_ws.send(JSON.stringify({"type": "req_logout", "data": {}}));
        },

        //websocket连接
        connect_core_ws: function(){
            var relogin = true; //允许重新登录
            var _this = this;
            this.core_ws = new WebSocket('ws://' + window.location.host + '/ws/autodrive/web/core/');
            this.core_ws.onopen = function(){
    //            tools.showMsgToast("websocket cnnected.", 3000);
                var userid = tools.getCookie('userid');
                var token = tools.getCookie('token');
                //        send_log("document.cookie: "+document.cookie);
                //        send_log("token: " + token);
                var data;
                if(typeof(token) == 'undefined' || typeof(userid) == 'undefined'){
                    loginInfo.innerHTML = "用户名或token不存在, 请勿禁用cookie";
                    // location.reload(); //重新加载页面已获得cookie

                    console.log("用户名或token不存在, 请勿禁用cookie");
                    return;
                }
                data = JSON.stringify({"type": "req_login", "data": {"userid": userid, "token": token}});
                tools.send_log(data);
                _this.core_ws.send(data);
            };

            this.core_ws.onmessage = function(evt){
                tools.receive_log("ws:" + evt.data)
                var code, type, msg;

                try{ //json解析 异常捕获
                    var message = JSON.parse(evt.data);
                    type = message.type;
                    data = message.data;
                    code = message.code;
                    if(typeof(type) == "undefined")
                        return;
                }catch(err){
                    return;
                }

                // 登录反馈
                if(_this.core_ws_login==0 && type=="res_login"){
                    if(code == 0){ // 登录成功
                        _this.core_ws_login = 1;
                        connectBtn.name = "disconnect";
                        connectBtn.innerHTML = "断开";
                        loginInfo.innerHTML = "登录成功";
                        return;
                    }else{
                        loginInfo.innerHTML = "帐号或密码/token错误";
                        location.reload(); //登录帐号以及token均是从cookie获取, 正常不会出错, 如验证失败, 刷新页面以重新获取cookie
                        console.log("帐号或密码/token错误");
                    }
                }
                else if(type == "rep_force_offline"){
                    _this.core_ws_initiative_close = 1;
                    _this.core_ws.close();  //先关闭连接, 再alert, 因为alert是阻塞的
                    alert("异处登录，您已被迫下线，可刷新页面重新登录");
                    loginInfo.innerHTML = "异处登录，您已被迫下线，可刷新页面重新登录!";
                    location.reload();
                }
                else if(type == "rep_car_state"){
                  // 状态数据
                  // info.id
                  // info.car_state

                  $('#taskCarState').val(data.status);  //自动驾驶任务状态
                }
                else if(type == "res_car_list"){
    //                console.log(msg.cars)
                    showOnlineCars(msg.cars)
                }
            };
            this.core_ws.onclose = function(evt){
                // 更新状态数据显示
                if(_this.core_ws_login)
                {
                    connectBtn.name = "connect";
                    connectBtn.innerHTML = "连接";
                    _this.core_ws_login = 0;
                }
                // 如果非主动关闭(网络错误等),则尝试再次登录
                // 若不进行重连, 实时信息将无法接收
                if(_this.core_ws_initiative_close == 0){
                    console.log("core_ws close, try to reconnect");
                    _this.connect_core_ws();
                }
            };
        },
    };

    index.init();
})();


function showOnlineCars(cars){

    // 在线靠前排序
    cars.sort(function(a,b){
        return b.online - a.online;
    });

    console.log(cars);
    var tab="<table border='1'>";
    tab+="<tr><th>车辆ID</th><th>车辆名称</th><th>" +"<input type='checkbox' " + "id='showAllCarsPos'>显示位置"+"</th>"
        +"<th>是否在线</th>"+"<th>分组</th>"
        +"</tr>";

    for(var i in cars){
        tab += "<tr>";
            tab += "<td><u class='doTask'>" + cars[i].id + "</u></td>";
            tab += "<td>" + cars[i].name + "</td>";

            if(cars[i].online){
                tab += "<td><input type='checkbox' " +"class='showCarPos' name='" + cars[i].id + "'/>显示位置"+"</td>";
                tab += "<td>在线</td>";
            }else{
                tab += "<td><input type='checkbox' disabled='disabled' class='no-showCarPos' name='" + cars[i].id + "'/>显示位置"+"</td>";
                tab += "<td>离线</td>";
            }

            tab += "<td>" + cars[i].group + "</td>"
        tab += "</tr>"
    }
    tab+="</table>";

    var divv=document.getElementById("cars_list");
    divv.innerHTML=tab;
}
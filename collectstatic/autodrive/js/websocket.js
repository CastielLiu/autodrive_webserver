
var g_core_ws;
var g_core_ws_login = 0;


// body加载后自动调用
function onBodyLoad(){
    connect_core_ws();
}

// 关闭所有的WebSocket
// 一般在用户注销登录后断开， 但若注销后页面自动跳转，则无需手动断开，句柄将自动释放
function disconnect_ws(){
    g_core_ws.close();
}

function connect_core_ws_backup(){
    g_core_ws = new WebSocket('ws://' + window.location.host + '/autodrive/web/core/');
    g_core_ws.onopen = function(){
//        tools.showMsgToast("websocket cnnected.", 3000);
        var token = tools.getCookie('token');
//        send_log("document.cookie: "+document.cookie);
//        send_log("token: " + token);
        var data;
        if(username.value == "" || password.value == ""){
            if(typeof(token) == 'undefined'){
                loginInfo.innerHTML = "无令牌, 请输入帐号和密码";
                return;
            }
            else{
                data = JSON.stringify({"type": "req_login", "msg": {"username": active_username.innerHTML, "token": token}});
            }
        }else{
            data = JSON.stringify({"type": "req_login", "msg": {"user_id": username.value, "password": password.value}})
        }
        send_log(data);
        g_core_ws.send(data)
    };

    g_core_ws.onmessage = function(evt){
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

      receive_log(JSON.stringify(data))

      // 登录反馈
      if(g_core_ws_login==0 && type=="res_login"){
        if(msg.result){ // 登录成功
            g_core_ws_login = 1;
            connectBtn.name = "disconnect";
            connectBtn.innerHTML = "断开";
            loginInfo.innerHTML = "登录成功";

            // requestOnlineCars(); //http
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
        showOnlineCars(msg.cars)
      }
    }

    g_core_ws.onclose = function(evt){
        if(g_core_ws_login)
        {
            connectBtn.name = "connect";
            connectBtn.innerHTML = "连接";
            g_core_ws_login = 0;
            loginInfo.innerHTML = "";
        }
    }
}

function connect(){
    loginInfo.innerHTML = "";
    if(connectBtn.name == "connect"){
        connect_core_ws();
    }else{
        connectBtn.name = "connect";
        connectBtn.innerHTML = "连接";
        g_core_ws.close();
        g_core_ws_login = 0;
    }
}

//function getOnlineCars(){
//    type = "req_online_car";
//    var request = {"type": type};
//    g_core_ws.send(JSON.stringify(request));
//}



function listenCar(obj){
    var type = "req_listen_car";
    var car_id = obj.name;
    var listen_cars;
    var request = {"type": type, "msg": listen_cars};
    if(obj.checked){
        listen_cars = {"cars": [{"car_id": car_id, "on": 1},]};
    }
    else{
        listen_cars = {"cars": [{"car_id": car_id, "on": 0},]};
    }
    request_text = JSON.stringify(request);
    send_log(request_text);

    g_core_ws.send(request_text); //ws

}

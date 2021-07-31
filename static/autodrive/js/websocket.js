
var g_ws;
var g_ws_login = 0;

// 调试显示
function receive_log(str_msg){
    document.querySelector('#receive_log').value += (str_msg + '\n');
    receive_log.scrollTop = receive_log.scrollHeight;
}

function send_log(str_msg){
    document.querySelector('#send_log').value += (str_msg + '\n');
    send_log.scrollTop = send_log.scrollHeight;
}

function getCookie(key){
    var key_values = document.cookie.split(';');

    for(var i=0; i<key_values.length; i++) {
        key_value = key_values[i].split('=');
        if(key_value[0] == key)
            return key_value[1];
    }
    return "";
}

function load(){
    connect_core_ws();
}

function connect_core_ws(){
    g_ws = new WebSocket('ws://' + window.location.host + '/autodrive/web/core/');
    g_ws.onopen = function(){
        var token = getCookie('token');
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
        g_ws.send(data)
    };

    g_ws.onmessage = function(evt){
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
      if(g_ws_login==0 && type=="res_login"){
        if(msg.result){ // 登录成功
            g_ws_login = 1;
            connectBtn.name = "disconnect";
            connectBtn.innerHTML = "断开";
            loginInfo.innerHTML = "登录成功";
//            getOnlineCars();  //ws

            requestOnlineCars(); //http
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

    g_ws.onclose = function(evt){
        if(g_ws_login)
        {
            connectBtn.name = "connect";
            connectBtn.innerHTML = "连接";
            g_ws_login = 0;
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
        g_ws.close();
        g_ws_login = 0;
    }
}

function getOnlineCars(){
    type = "req_online_car";
    var request = {"type": type};
    g_ws.send(JSON.stringify(request));

    request_text = JSON.stringify(request);
    send_log(request_text)
}

function requestListenCars(car_id){
    var type = "req_listen_car";
    var listen_car1 = {"id": "seu_ant", "attr":['speed','steer_angle']};
    var listen_car2 = {"id": "seu_ant1", "attr":['a1','b1']};
    var listen_cars = {"cars": [listen_car1, listen_car2]};
    var request = {"type": type, "msg": listen_cars};
    g_ws.send(JSON.stringify(request));
    //{"type":"request_car_info","msg":{"cars":[{"id":"xx","attr":["a","b"]},{"id":"xxx","attr":["a1","b1"]}]}}
}

function showOnlineCars(cars){
    var tab="<table border='1'>";
    tab+="<tr><th>车辆ID</th><th>车辆名称</th><th>显示状态</th></tr>"

    for(var i in cars){
        tab+=("<tr><td>" + cars[i].id + "</td><td>" + cars[i].name + "</td><td>"
            +"<input type='checkbox' " +"name=" + cars[i].id + " onchange='listenCar(this)'>显示状态"+"</td></tr>")
    }
    tab+="</table>";
    var divv=document.getElementById("onlineCars");
    divv.innerHTML=tab;
}


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

    g_ws.send(request_text); //ws

}

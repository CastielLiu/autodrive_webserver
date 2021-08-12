function HttpRequest2(obj) {
    var headers = {
        // csrf防御请求头
        'X-CSRFToken': tools.getCookie('csrftoken'),

    };

    return $.ajax({
        url: obj.url || "",
        type: obj.type || 'POST',
        headers: headers,
        async: obj.async || true,
        dataType: obj.dataType || '',
        timeout:90000,
        data: JSON.stringify(obj.cmd),

        success: function(data){
            tools.receive_log("http: " + data)
            obj.done(data);
        },
    })
};


//获取http请求对象
function getXMLHttpRequest(){
    var xmlhttp = null;
    if (window.XMLHttpRequest){// code for all new browsers
        xmlhttp=new XMLHttpRequest();
    }
    else if (window.ActiveXObject){// code for IE5 and IE6
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    return xmlhttp;
}

function HttpRequest(obj){
    request = getXMLHttpRequest();
    if (request == null)
        return;

    request.open(obj.method || "POST", obj.url || "", obj.async || true);

    // 添加此请求头以通过csrf防御
    request.setRequestHeader("X-CSRFToken", tools.getCookie('csrftoken')); // open之后才能设置请求头

    tools.send_log("http: " + JSON.stringify(obj.cmd));

    request.send(JSON.stringify(obj.cmd));
    request.onreadystatechange=function(){
        if(request.readyState!=4)
            return;
        obj.done(request.responseText);
        tools.receive_log("http: " + request.responseText)
    }
}

//请求获取在线车辆列表
function requestOnlineCars(group){
    request = getXMLHttpRequest();
    if (request == null)
        return;
    cmd = {"type":"req_online_car", "data": {"group": group}};

    request.open("POST", "", true);
    request.send(JSON.stringify(cmd));

    request.onreadystatechange=function(){
        if(request.readyState!=4)
            return;
        dict = JSON.parse(request.responseText);
        console.log(dict);
        type = dict.type;
        code = dict.code;
        msg = "";
        if(code === 0)
            showOnlineCars(dict.data.cars)
        else if(code === 7)
            msg = "无请求权限";
        else if(code === 2)
            msg = "无在线车辆";

    }
}

//请求监听车辆信息
function requestListenCars(car_id){
    var type = "req_listen_car";
    var listen_car1 = {"id": "seu_ant", "attr":['speed','steer_angle']};
    var listen_car2 = {"id": "seu_ant1", "attr":['a1','b1']};
    var listen_cars = {"cars": [listen_car1, listen_car2]};
    var request = {"type": type, "data": listen_cars};
    g_core_ws.send(JSON.stringify(request));
    //{"type":"request_car_info","msg":{"cars":[{"id":"xx","attr":["a","b"]},{"id":"xxx","attr":["a1","b1"]}]}}
}

function requestPathList(group){
    tools.send_log(group);
    HttpRequest({
        cmd: {"type":"req_path_list", "data": {"group": group}},
        url: "",
        done: function(data){
            dict = JSON.parse(data);
            if(dict.code != 0)
                return;

            var obj = document.getElementById("pathList");
            obj.options.length = 0;  // 删除所有option
            path_list = dict.data.path_list;
            for(let idx=0; idx<path_list.length; idx++){
                path = path_list[idx];
                obj.add(new Option(path.name, path.id))
            }
        }
    });
}

function requestPath(pathid){
    HttpRequest({
        cmd: {"type":"req_path", "data": {"pathid": pathid}},
        url: "",
        done: function(data){
            dict = JSON.parse(data);
        }
    });
}

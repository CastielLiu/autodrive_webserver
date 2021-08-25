
// AJAX请求 jQuery
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

        success: function(data, status, xhr){
            redirect_url = xhr.getResponseHeader('Redirect');
//            tools.receive_log(redirect_url);
            if(typeof(redirect_url)=='string' && redirect_url.length>0){
                window.location.href = redirect_url;
            }else{
//                tools.receive_log("http: " + data);
                obj.done(data);
            }
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

// AJAX请求 JS
function HttpRequest(obj){
    xhr = getXMLHttpRequest();
    if (xhr == null)
        return;

    xhr.open(obj.method || "POST", obj.url || "", obj.async || true);

    // 添加此请求头以通过csrf防御
    xhr.setRequestHeader("X-CSRFToken", tools.getCookie('csrftoken')); // open之后才能设置请求头

    tools.send_log("http: " + JSON.stringify(obj.cmd));

    xhr.send(JSON.stringify(obj.cmd));
    xhr.onreadystatechange=function(){
        if(xhr.readyState!=4)
            return;

        redirect_url = xhr.getResponseHeader('Redirect');
        //判断是否为重定向应答
        if(typeof(redirect_url)=='string' && redirect_url.length>0){
            window.location.href = redirect_url; //加载重定向url
        }else{
            tools.receive_log("http: " + xhr.responseText);
            obj.done(xhr.responseText);
        }
    }
}

//请求获取在线车辆列表
function requestOnlineCars(group){
    HttpRequest2({
        cmd: {"type":"req_online_car", "data": {"group": group|""}},
        url: "",
        done: function(data){
            dict = JSON.parse(data);
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
    });
}

//请求获取车辆位置, 并按需绘制
function requestCarsPosition(){
    cars_id = []

    // 提取被勾选的车辆
    $(".showCarPos").each(function () {
        if($(this).prop("checked")){
            cars_id.push($(this).attr("name"));
        }
    });
//    console.log(cars_id)

    HttpRequest2({
        cmd: {"type":"req_cars_pos", "data": {"cars_id": cars_id}},
        url: "",
        done: function(data){
            dict = JSON.parse(data);
            type = dict.type;
            code = dict.code;
            msg = "";
            if(code === 0){
                window.mapctrler.addCarsMarker(dict.data.cars_pos);
            }
        }
    });
}

//请求获取路径轨迹
function requestPathLine(pathid){

    HttpRequest2({
        cmd: {"type":"req_path_line", "data": {"path_id": pathid}},
        url: "",
        done: function(data){
            dict = JSON.parse(data);
            type = dict.type;
            code = dict.code;
            msg = "";
            if(code === 0){
                window.mapctrler.addPathLine(dict.data.points);
            }
        }
    });
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
//    tools.send_log(group);
    HttpRequest2({
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

function requestPathTraj(pathid){
    HttpRequest({
        cmd: {"type":"req_path_traj", "data": {"pathid": pathid}},
        url: "",
        done: function(data){
            dict = JSON.parse(data);
        }
    });
}

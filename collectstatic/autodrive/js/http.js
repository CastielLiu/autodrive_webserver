
// AJAX请求 jQuery
function HttpRequest2(obj) {
    var headers = {
        // csrf防御请求头
        'X-CSRFToken': tools.getCookie('csrftoken'),
    };
//    console.log(typeof(obj.async)=="undefined");
//    console.log(obj.async || true);
    return $.ajax({
        url: obj.url || "",
        type: obj.type || 'POST',
        headers: headers,
        async: typeof(obj.async)=="undefined" ? true : obj.async,
        timeout: typeof(obj.timeout)=="undefined" ? 0 : obj.timeout,
        dataType: obj.dataType || '',
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
        // 请求成功失败都会执行complete
        complete: obj.complete || function(xhr, status){},
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
        cmd: {"type":"req_car_list", "data": {"group": group|""}},
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
                // 'cars_pos': [{'car_id': xx, 'lat': xx, 'lng': xx, 'online': xx}]
                var cars_pos = dict.data.cars_pos;
                var BMapPointsWGS84 = [];
                for(var i = 0, pointsLen = cars_pos.length; i < pointsLen; i++){
                    BMapPointsWGS84.push(new BMap.Point(cars_pos[i].lng, cars_pos[i].lat));
                }
                window.mapctrler.addCarsMarkerWGS84(cars_pos, {points: BMapPointsWGS84, status: 0});
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
        cmd: {"type":"req_path_list", "data": {"groupid": window.index.user_groupid}},
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

//请求获取路径轨迹
function requestPathTraj(pathid){
    HttpRequest({
        cmd: {"type":"req_path_traj", "data": {"path_id": pathid}},
        url: "",
        done: function(data){
            dict = JSON.parse(data);
            type = dict.type;
            code = dict.code;
            msg = "";
            if(code === 0){
                var pathid = dict.data.id;
                var path_name = dict.data.name;

                window.mapctrler.addPathLineWGS84({id: pathid, name: path_name, batch: 0}, {points: dict.data.points, status: 0});
            }
        },
    });
}

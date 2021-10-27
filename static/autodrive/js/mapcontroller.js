(function(){

    window.map = new BMap.Map("baidumap_container", {
            minZoom: 5,
            maxZoom: 19,
    });
    // 创建位置检索、周边检索和范围检索 https://blog.csdn.net/dk123sw/article/details/81095347
    window.local_map = new BMap.LocalSearch(
        window.map,
        {
            //字典可能被回调使用, map参数无法使用this.map
            renderOptions: {map: window.map, autoViewport: true},
            onSearchComplete: function(results){
                if (window.local_map.getStatus() == BMAP_STATUS_SUCCESS){
                   console.log("search success");
                }
                else{
                    console.log("search failed");
                }
            }
        }
    );

    var mapctrler = window.mapctrler = {
        // 在指定容器创建地图实例并设置最大最小缩放级别
        map: window.map,

        init: function(){
            // 设置地图主题
            //默认地图样式(normal)
            //清新蓝风格(light)
            //黑夜风格(dark)
            //清新蓝绿风格(bluish)
            //高端灰风格(grayscale)
            //强边界风格(hardedge)
            //青春绿风格(darkgreen)
            //浪漫粉风格(pink)
            //午夜蓝风格(midnight)
            //自然绿风格(grassgreen)
            //精简风格(googlelite)
            //红色警戒风格(redalert)
            this.map.setMapStyle({style : "normal"});  // some error

            // 初始化地图，设置中心点和显示级别
            //this.map.centerAndZoom(new BMap.Point(116.316967, 39.990748), 15);
            this.map.centerAndZoom(new BMap.Point(120.16575, 33.3794), 17);

            // 开启鼠标滚轮缩放功能, 仅对PC上有效
            this.map.enableScrollWheelZoom(true);
            // 将控件（平移缩放控件）添加到地图上
//            this.map.addControl(new BMap.NavigationControl());

            // 为地图增加点击事件，为input赋值
            this.map.addEventListener("click", function(e) {
                document.getElementById('lat').value = e.point.lat;
                document.getElementById('lng').value = e.point.lng;
            });
        },

        // 发起位置检索
        locationSearch: function() {
            var city = $("#cityName").val();
            if (city != "") {
                window.local_map.search(city);
                console.log(city);
            }
        },

        // 弹出经纬度
        submit: function() {
            var lat = document.getElementById('lat');
            var lng = document.getElementById('lng');
            alert("经度：" + lng.value + "\n" + "纬度：" + lat.value);
        },

        getCar: function() {
            _this = this;
            $.ajax({
                url: "/car_state",
                timeout: 10000, //超时时间设置为10秒；
                dataType:"json",
                success: function(data) {
                    var points = data;
                    _this.addMarker(points);
                },
                error: function(xhr, type, errorThrown) {
                }
            });
        },

        getPath: function() {
            $.ajax({
                url: "/nav_path",
                timeout: 10000, //超时时间设置为10秒；
                dataType:"json",
                success: function(data) {
                    var pointArr = data;
                    addLine(pointArr);
                    // setZoom({points: pointArr});
                },
                error: function(xhr, type, errorThrown) {

                }
            });
        },

        removeOverlay: function(id, only_one=true){
            var allOverlays = map.getOverlays();
            for (var i = 0; i < allOverlays.length; i++){
                if(allOverlays[i].id == id){
                    this.map.removeOverlay(allOverlays[i]);
                    if(only_one){
                        return;
                    }
                }
            }
        },

        // 利用BD09坐标 创建图标对象
        addCarsMarkerBD09: function(cars_pos, data){
            if(data.status != 0){
                return;
            }

            var points = data.points;
            var car_id, point, marker;
            // 创建标注对象并添加到地图
            for (var i = 0, len = points.length; i < len; i++) {
                car_id = cars_pos[i].car_id;
                point = points[i];
//                console.log(point);
                // 判断正常或者故障，根据不同装填显示不同Icon
                var myIcon = new BMap.Icon("/static/autodrive/imgs/normal.png", new BMap.Size(32, 32), {
                        // 指定定位位置
                        offset: new BMap.Size(16, 32),
                        // 当需要从一幅较大的图片中截取某部分作为标注图标时, 需要指定大图的偏移位置
                        // imageOffset: new BMap.Size(0, -12 * 25)
                    });
                // 创建一个图像标注实例
                var marker = new BMap.Marker(point, {
                    icon: myIcon
                });
                marker.id = car_id;

                this.removeOverlay(marker.id);
                //创建marker点的标记,这里注意下,因为百度地图可以对label样式做编辑,
                var label = new BMap.Label(marker.id, {offset: new BMap.Size(20, 0)});
                //label.setStyle({display: "none"}); //对label样式隐藏
                marker.setLabel(label); //把label设置到maker上
                // 将覆盖物添加到地图上
                this.map.addOverlay(marker);
                // this.map.centerAndZoom(point, 17);

                // 添加信息弹窗
                // marker.openInfoWindow(new BMap.InfoWindow(car_id, {width: 50, height: 25}));
                var sContent = "车辆ID:" + car_id + "<br>速度: 0.0km/h";
                var opts = {
                    width: 120, // 信息窗口宽度
                    height: 125, // 信息窗口高度
                    title: '<h>'+'测试标题'+'</h>', // 信息窗口标题
                    enableMessage: false, //设置允许信息窗发送短息
                    message: ""
                }
                // 创建信息窗口对象
                var infoWindow = new BMap.InfoWindow(sContent, opts);
                // 添加点击事件
                marker.addEventListener("click", function() {
                    marker.openInfoWindow(infoWindow); //开启信息窗口
                });
            }
        },

        // 利用wgs84坐标 创建图标对象
        addCarsMarkerWGS84: function(cars_pos, data) {
            var points = data.points;
            // 'cars_pos': [{'car_id': xx, 'lat': xx, 'lng': xx, 'online': xx}]
            _this = this;

            // 调用百度API将WGS84转为BD09
            var convertor = new BMap.Convertor();
            convertor.translate(points, 1, 5, _this.addCarsMarkerBD09.bind(_this, cars_pos));
        },

        path_points : [], // 存储即将需要聚焦的路径点集
        addPathLineDB09: function(path_info, data){
            console.log(path_info, data);
            if(data.status != 0){
                return;
            }
            var points = data.points;
            var polyline = new BMap.Polyline(points, {
                strokeColor: "#0C8816",
                // strokeColor: "blue",
                strokeWeight: 3,
                setStrokeStyle: "dashed",
                strokeOpacity: 1
            });

            polyline.id = "path";

            if(path_info.batch == 1){
                //mapctrler.removeOverlay(polyline.id, false); //移除所有历史绘制的轨迹
                mapctrler.path_points = points;
            }
            else if(path_info.batch == path_info.total_bacths){
                mapctrler.path_points = mapctrler.path_points.concat(points);
                mapctrler.setZoom({points: mapctrler.path_points});
            }
            else
                mapctrler.path_points = mapctrler.path_points.concat(points);

             // 将覆盖物（线）添加到地图上
            this.map.addOverlay(polyline);
        },

        addPathLineWGS84: function(path_info, data) {
            console.log(path_info, data.points);
            if(data.status != 0){
                return;
            }
            _this = this;
            var points = data.points;
            if(points.length == 0)
                return;

            // wgs84 转 BD09
            // 由于每次只能转换10个坐标点, 分批进行转换
            var convertor = new BMap.Convertor();
            var batchs = Math.ceil(points.length / 10.0)
            var middle_point = new BMap.Point(0, 0); //中间点,用于定位聚焦

            this.removeOverlay("path", false); //移除所有历史绘制的轨迹
            for(var k=0; k<batchs; k++){
                var BMapPointsWGS84 = [];
                for(var i=10*k; i<10*(k+1)&&i<points.length; i++){
                    BMapPointsWGS84.push(new BMap.Point(points[i].lng, points[i].lat));
                    middle_point.lat += points[i].lat /= points.length;
                    middle_point.lng += points[i].lng /= points.length;
                }
                var new_path_info = Object.assign({}, path_info);
                new_path_info.batch = k+1;
                new_path_info.total_bacths = batchs;
                convertor.translate(BMapPointsWGS84, 1, 5, _this.addPathLineDB09.bind(_this, new_path_info));
            }

            //tools.console_log(middle_point);
            //convertor.translate([middle_point], 1, 5, _this.setZoom);
        },

        //根据经纬极值计算绽放级别
        getZoom: function(maxLng, minLng, maxLat, minLat) {
            // 级别18到3。
            var zoom = ["50", "100", "200", "500", "1000", "2000", "5000", "10000", "20000",
                        "25000", "50000", "100000", "200000", "500000", "1000000", "2000000"];
            // 创建点坐标A
            var pointA = new BMap.Point(maxLng, maxLat);
            // 创建点坐标B
            var pointB = new BMap.Point(minLng, minLat);
            //获取两点距离,保留小数点后两位
            var distance = this.map.getDistance(pointA, pointB).toFixed(1);
            for (var i = 0, zoomLen = zoom.length; i < zoomLen; i++) {
                if (zoom[i] - distance > 0) {
                    //之所以会多3，是因为地图范围常常是比例尺距离的10倍以上。所以级别会增加3。
                    return 18 - i + 4;
                }
            }
        },

        // 判断最大和最小经纬度, 然后进行聚焦显示
        setZoom: function(data) {
            tools.console_log("setZoom");
            tools.console_log(data);
            var points = data.points;
            if (points.length > 0) {
                var maxLng = points[0].lng;
                var minLng = points[0].lng;
                var maxLat = points[0].lat;
                var minLat = points[0].lat;
                var res;
                for (var i = points.length - 1; i >= 0; i--) {
                    res = points[i];
                    if (res.lng > maxLng) maxLng = res.lng;
                    if (res.lng < minLng) minLng = res.lng;
                    if (res.lat > maxLat) maxLat = res.lat;
                    if (res.lat < minLat) minLat = res.lat;
                }
                var cenLng = (parseFloat(maxLng) + parseFloat(minLng)) / 2;
                var cenLat = (parseFloat(maxLat) + parseFloat(minLat)) / 2;
                var zoom = mapctrler.getZoom(maxLng, minLng, maxLat, minLat);
                this.map.centerAndZoom(new BMap.Point(cenLng, cenLat), zoom);
            } else {
                this.map.centerAndZoom(new BMap.Point(116.316967, 39.990748), 15);
            }
        },
    };
    mapctrler.init();
})();


//getCar()
//getPath()
//setInterval(getCar, 1000)
//setInterval(getPath, 1000)

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
            // 初始化地图，设置中心点和显示级别
            //this.map.centerAndZoom(new BMap.Point(116.316967, 39.990748), 15);
            this.map.centerAndZoom(new BMap.Point(118.822011, 31.892611), 17);

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

        getPath: function getPath() {
            $.ajax({
                url: "/nav_path",
                timeout: 10000, //超时时间设置为10秒；
                dataType:"json",
                success: function(data) {
                    var pointArr = data;
                    addLine(pointArr);
                    // setZoom(pointArr);
                },
                error: function(xhr, type, errorThrown) {

                }
            });
        },

        // 创建图标对象
        addCarsMarker: function(cars) {
            _this = this;
            //'cars': [{'id': xx, 'lat': xx, 'lng': xx}]
            var point, marker;
            // 创建标注对象并添加到地图
            for (var i = 0, pointsLen = cars.length; i < pointsLen; i++) {

                point = new BMap.Point(cars[i].lng, cars[i].lat);
                // 判断正常或者故障，根据不同装填显示不同Icon
                var myIcon = new BMap.Icon("static/imgs/normal.png", new BMap.Size(32, 32), {
                        // 指定定位位置
                        offset: new BMap.Size(16, 32),
                        // 当需要从一幅较大的图片中截取某部分作为标注图标时，需要指定大图的偏移位置
                        //imageOffset: new BMap.Size(0, -12 * 25)
                    });
                // 创建一个图像标注实例
                marker = new BMap.Marker(point, {
                    icon: myIcon
                });
                // 将覆盖物添加到地图上
                this.map.addOverlay(marker);

                //给标注点添加点击事件
                marker.addEventListener("click", function() {
                    _this.showInfo(this, cars[i]);
                });
            }
        },

        //显示信息窗口，显示标注点的信息
        showInfo: function(thisMaker, car) {
            var sContent = '';
                sContent += '<ul class="info_ul info_ui_Nimg">';
                sContent += '   <li class="info_li">';
                sContent += '       <span class="info_span">车辆ID：</span>';
                sContent += '       <span>' + car.id + '</span>';
                sContent += '   </li>';
                sContent += '   <li class="info_li">';
                sContent += '       <span class="info_span">车辆名称：</span>';
                sContent += '       <span>' + car.name + '</span>';
                sContent += '   </li>';
                sContent += '   <li class="info_li">';
                sContent += '       <span class="info_span">车辆速度：</span>';
                sContent += '       <span>' + car.speed + '</span>';
                sContent += '   </li>';
                sContent += '</ul>';
            // 创建信息窗口对象
            var infoWindow = new BMap.InfoWindow(sContent);

            //图片加载完毕重绘infowindow
            thisMaker.openInfoWindow(infoWindow);
        },


        // 弹窗增加点击事件
//        function func(data) {
//            alert("点击了机器编号为：" + data + "\n");
//        }

        addLine: function(pointArr) {
            // 使用浏览器的矢量图制图工具，在地图上绘制折线的地图叠加层
            var polyline = new BMap.Polyline(pointArr.path, {
                strokeColor: "#0C8816",
                // strokeColor: "blue",
                strokeWeight: 3,
                setStrokeStyle: "dashed",
                strokeOpacity: 1
            });

            // 将覆盖物（线）添加到地图上
            this.map.addOverlay(polyline);

            //
            for (var i = 0, j = pointArr.path.length; i < j; i++) {

                myIcon = new BMap.Icon("static/images/normal.png", new BMap.Size(32, 32), {
                    // 指定定位位置
                    offset: new BMap.Size(10, 32),
                });
                // console.log(pointArr.path[i]);
                var point = new BMap.Point(pointArr.path[i].lng,pointArr.path[i].lat)
                // var point = new BMap.Point(116.324045, 39.987984);
                var marker = new BMap.Marker(point, {
                    icon: myIcon
                });

                this.map.addOverlay(marker);
            };
        },

        //根据经纬极值计算绽放级别
        getZoom: function(maxLng, minLng, maxLat, minLat) {
            // 级别18到3。
            var zoom = ["50", "100", "200", "500", "1000", "2000", "5000", "10000", "20000", "25000", "50000", "100000", "200000", "500000", "1000000", "2000000"];
            // 创建点坐标A
            var pointA = new BMap.Point(maxLng, maxLat);
            // 创建点坐标B
            var pointB = new BMap.Point(minLng, minLat);
            //获取两点距离,保留小数点后两位
            var distance = this.map.getDistance(pointA, pointB).toFixed(1);
            for (var i = 0, zoomLen = zoom.length; i < zoomLen; i++) {
                if (zoom[i] - distance > 0) {
                    //之所以会多3，是因为地图范围常常是比例尺距离的10倍以上。所以级别会增加3。
                    return 18 - i + 3;
                }
            }
        },

        // 判断最大和最小经纬度
        setZoom: function(points) {
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
                var zoom = getZoom(maxLng, minLng, maxLat, minLat);
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

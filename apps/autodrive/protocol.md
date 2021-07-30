# websocket 用户协议
## 1. 请求与响应格式
### 1.1 客户端消息格式
{"type": type, "msg": msg, ...}

|  参数    | 值  |  描述  |
|  ----  | ----  | --- |
| type  | req_login: 请求登录</br>req_logout: 请求注销</br>req_online_car: 请求在线车辆列表</br>req_listen_car: 请求监听车辆信息   </br></br>rep_car_state: 上报车辆状态信息| 消息类型</br>req_: 请求</br>res_: 应答</br>rep_: 上报|
| msg  | {} | json格式消息体，可选参数|

### 1.2 服务器消息格式 
{"type": type, "msg", msg, ...}

|  参数    | 值  |  描述  |
|  ----  | ----  | --- |
| type  | res_login: 响应客户端登录</br>res_online_car: 响应在线车辆列表</br>res_listen_car: 响应监听车辆信息</br></br>rep_car_state: 上报车辆信息| 消息类型</br>req_: 请求</br>res_: 应答</br>rep_: 上报|
| msg  | {} | json格式消息体，可选参数|

## 2. 请求与响应消息体msg
### 2.1 请求登录 req_login 响应登录 res_login
客户端: {"use_name": xxx, "user_id": xxx "password": xxx}  use_name与user_id有一即可，password必填\
服务端: {"result": True, "info": xx} 登录成功？ 消息反馈

### 2.2 请求注销 req_logout 响应注销 res_logout
客户端: 空
服务端: 空

### 2.3 请求在线车辆列表 req_online_cars 响应 res_online_cars
客户端: 空
服务端: {"cars": [{"id": xx, "name": xx}, {"id": xx, "name": xx}, ...]}

### 2.4 请求监听车辆数据 req_listen_car 响应 res_listen_car
客户端: {"cars": [{"id": xx, "attr": ["speed", "angle", ...]}, ...]}\
&emsp; 车辆id,以及需要获取车辆数据的属性attr, 此字段信息应与车辆数据名称保持一致\
&emsp; attr分别有: speed, steer_angle,  \
&emsp; 当attr为空时, 停止监听, 当attr不存在时监听所有数据\
&emsp; cars的数据上报更新频率由服务器固化
服务端: 空

车端定时向服务器上报数据可能导致流量消耗较大, 当没有用户监听时, 可延迟上报/部分上报/不上报
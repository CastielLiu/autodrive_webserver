var tools = {
    // 显示消息弹窗
    showMsgToast: function(msg, duration){
        duration = isNaN(duration)?3000:duration;
        var m = document.createElement('div');
        m.innerHTML = msg;
        m.style.cssText="width:60%; min-width:180px; background:#000; opacity:0.6; height:auto;min-height: 30px; color:#fff; line-height:30px; text-align:center; border-radius:4px; position:fixed; top:60%; left:20%; z-index:999999;";
        document.body.appendChild(m);
        setTimeout(function() {
            var d = 0.5;
            // 设置渐变
            m.style.webkitTransition = '-webkit-transform ' + d + 's ease-in, opacity ' + d + 's ease-in';
            m.style.opacity = '0';
            setTimeout(function() { document.body.removeChild(m) }, d * 1000);
        }, duration);
    },

    getCookie: function(key){
        var key_values = document.cookie.split(';');
//        console.log(key_values);
        for(var i=0; i<key_values.length; i++) {
            key_value = key_values[i].split('=');
//            console.log(key_value[0].trim());
            if(key_value[0].trim() == key)  //分割后的字符串前后可能存在空格
                return key_value[1];
        }
        return "";
    },

    // 调试显示
    receive_log: function(str_msg){
        document.querySelector('#receive_log').value += (str_msg + '\n');
        receive_log.scrollTop = receive_log.scrollHeight;
    },

    send_log: function(str_msg){
        document.querySelector('#send_log').value += (str_msg + '\n');
        send_log.scrollTop = send_log.scrollHeight;
    },

}

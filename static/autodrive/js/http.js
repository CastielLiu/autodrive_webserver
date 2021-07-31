
function getXmlhttp(){
    var xmlhttp = null;
    if (window.XMLHttpRequest){// code for all new browsers
        xmlhttp=new XMLHttpRequest();
    }
    else if (window.ActiveXObject){// code for IE5 and IE6
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    return xmlhttp;
}


function requestOnlineCars(){
    xmlhttp = getXmlhttp();
    if (xmlhttp == null)
        return;

    xmlhttp.open("POST", "", true);
    xmlhttp.send('{"type":"req_online_car"}');

    xmlhttp.onreadystatechange=function(){
        if(xmlhttp.readyState!=4)
            return;
        data = JSON.parse(xmlhttp.responseText);
        type = data.type;
        msg = data.msg;
        showOnlineCars(msg.cars)
    }
}
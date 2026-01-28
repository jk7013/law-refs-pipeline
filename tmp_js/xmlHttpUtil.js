var xmlHttp;
var procObj;
/**
  * xmlHttp 생성
  */
function createXMLHttpRequest() {
    if (window.ActiveXObject) {
        xmlHttp = new ActiveXObject("Microsoft.XMLHTTP");
    }
    else if (window.XMLHttpRequest) {
        xmlHttp = new XMLHttpRequest();
    }
}
    
/**
  * xmlHttp 설정  
  * @param  url 경로 설정  , 다음 실행 함수
  */
function doRequestUsingPOST(urlTxt, notSync) {
    createXMLHttpRequest();
    var url = urlTxt+"&timeStamp=" + new Date().getTime();
    var queryString = "";
    xmlHttp.open("POST", url, !notSync);
    //xmlHttp.overrideMimeType("text/xml");
    if(!notSync) xmlHttp.onreadystatechange = handleStateChange;
    xmlHttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");    
    xmlHttp.send(queryString);
}
 
/**
  * xmlHttp 결과 처리  
  */    
function handleStateChange() {
	//alert(xmlHttp.readyState);
    if(xmlHttp.readyState == 4) {
        if(xmlHttp.status == 200) {
        	procObj();
        }
    }
}



 
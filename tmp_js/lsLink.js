/**
 * file_name: lsLink.js
 * summary	: 법령 링크 js
 * history	: 2019. 07. 18. [#16143] 자치법규 본문 링크 확인요청
 *	 		  2019. 08. 13. [#16302] 조문정보 이전과 비교 버그 수정요청 -> ajax 중복실행 방지
 *			  2019. 11. 21. [#18165] 자치법규에서 행정규칙으로 인용링크가 걸리도록 개선
 *			  2019. 11. 21. [#17838] 현행법령 서비스 개선
 *			  2019. 12. 12. [#18335] 이전과비교 버튼 확인
 *			  2020. 08. 06. [#20636] 연계정보 팝업에서 링크 오류 확인
 *			  2020. 09. 03. [#20683] 시행일 법령 HTML 재생성 개선
 *            2020. 09. 24. [#20889] 부칙 연계 기능 추가 요청
 *            2020. 10. 29. [#21280] 자치법규 링크 오류 확인
 *            2020. 11. 26. [#21510] 자치법규 링크 확인 요청
 *            2020. 12. 03. [#21590] 자치법규링크 확인
 *            2021. 04. 01. [#24068] 조문 연혁버튼 무한로딩 현상 확인
 *            2021. 05. 20. [#24521] 자치법규에서 조례 별표 링크가 정상적으로 열리지 않는 오류 확인
 * 			  2021. 06. 24. [#24851] 링크 팝업 사이즈 조정 가능 하도록 변경 요청
 * 			  2021. 06. 30. [#24957] 자치법규 본문 링크 수정
 *			  2021. 07. 15. [#25174] 자치법규 링크 오류 확인
 *			  2021. 12. 02. [#26269] 법령 본문 스크립트 오류 확인
 *            2021. 12. 16. [#26348] 법령 본문 조례위임 조문 버튼 오류
 *			  2022. 04. 14. [#28995] 공공기관 규정 연계 처리 요청
 *			  2022. 05. 19. [#29555] 위임규정 링크 조문단위로 생성할 수 있도록 개선
 *			  2022. 07. 14. [#30269] 행정심판례 링크 오류 확인
 *			  2023. 02. 16. [#31795] 링크 팝업 통일 요청
 *			  2023. 03. 02. [#32094] 자치법규에서 행정규칙으로 링크 오류 확인
 *			  2023. 03. 02. [#31795] 링크 팝업 통일 요청
 *			  2023. 04. 24. [#32591] 위임 행정규칙/규정 링크팝업화면과 본문팝업화면의 상단버튼이 다르게 노출되는 현상 확인요청
 * 			  2023. 07. 13. [#32939] 자치법규 링크 추출에 따른 팝업 화면 생성 로직 변경
 *			  2023. 09. 21. [#33137] 조례-조례시행규칙 위임관리 기능 개선요청
 *			  2024. 03. 28. [#34507] 연계정보 팝업창 내 링크 열리지 않는 오류 수정
 *			  2024. 03. 28. [#34523] 자치법규 조문링크 페이지에서 인쇄시 오류 수정
 *            2024. 08. 29. [#35232] 규제아이콘 행정망 서비스 요청
 *            2025. 02. 06. [#35850] 소스코드 보안약점 진단 처리 : 제거되지 않고 남은 디버그 코드
*/

var lnkTitle = "";
var $openPopWidth = "";
var $openPopHeight = "";
var LsLinkLayer = function(){
	var lsLinkLayer;
	return {
		showLsLinkLayer : function(size, title){
			if(size==0){
					if(lsLinkLayer){
						lsLinkLayer.dialog('close');
					}
					
					lsLinkLayer = $('#lsLinkLayer').dialog({
		            	autoOpen : false
		               ,width: 800
		               ,height: 300
		               ,modal: false
					   ,title: title
					   ,resizable: false
					   ,position: {
							// 내 객체 위치
							my : 'center',
							// 참조할 객체 위치
							at : 'center',
							// 참조할 객체 지정
							of : 'body'
						}
		            });
					
				lsLinkLayer.dialog("open");
				
				lsLinkLayer.show();
			}
			
		}
		,hiddenLsLinkLayer : function(){
			if(lsLinkLayer){
				lsLinkLayer.dialog("close");
			}
		}
		,returnLsLinkLayer : function(){
			return lsLinkLayer;
		}
	};
}();

/**
 * <pre>
 *  조문 팝업창 닫을 때, 조절된 창크기 저장
 * </pre>
 * @param widthTest
 * @param heightTest
 */
function setLsPopSize(popWidth, popHeight) {
	$openPopWidth = popWidth;
	$openPopHeight = popHeight;
}
/**
 * <pre>
 * 	법령링크 팝업 - BATCH(BatchCreateLsHtml)를 통해 생성된 HTML 링크에 대한 함수
 *  <shcho> ancYnChk 파라미터 추가
 * </pre>
 * @author brKim
 * @since 2017. 10. 11.
 * @param lsJoLnkSeq
 * @param docType
 */
function fncLsLawPop(lsJoLnkSeq, docType, ancYnChk) {
	var url = "lsLinkCommonInfo.do?lsJoLnkSeq="+lsJoLnkSeq;
	
	if (docType.substring(0,1) == "B") { //-- 별표/서식
		url = "lsLawLinkInfo.do?lsJoLnkSeq="+lsJoLnkSeq;
		openPop(url);
	} else if (docType == 'AR') { // 부칙
		url = "lsLawLinkInfo.do?lsJoLnkSeq="+lsJoLnkSeq;
		var popupX = (window.screen.width / 2) - (800 / 2);
		var popupY = (window.screen.height / 2) - (270 / 2);
		var win = window.open(url, '부칙정보', 'scrollbars=no,toolbar=no,resizable=no,status=no,menubar=no,width=800px,height=266px,left=' + popupX + ',top=' + popupY);
	}else if (docType == 'JO') { // 조문
		if($openPopWidth == null || $openPopWidth == "" && $openPopHeight == null || $openPopHeight == "") {
			url +="&chrClsCd=" + getValue("lsBdyChrCls") +"&ancYnChk=" + ancYnChk;
			var win = window.open(url, '조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=798px,height=681px');
		}else{
			url +="&chrClsCd=" + getValue("lsBdyChrCls") +"&ancYnChk=" + ancYnChk;
			var popupX = (window.screen.width / 2) - ($openPopWidth / 2);
			var popupY = (window.screen.height / 2) - ($openPopHeight / 2);
			var win = window.open(url, '조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=' + $openPopWidth + ',height=' + $openPopHeight);
		}
	}else if (docType == 'ALLJO' || docType == 'XX') { // 법령
		url +="&chrClsCd=" + getValue("lsBdyChrCls") +"&ancYnChk=" + ancYnChk;
		openPop(url,1000);
	}
}
/**
 * <pre>
 * 	법령링크 팝업 (수동링크는 fncLsPttnLinkPop으로 이동)
 * </pre>
 * @author brKim
 * @since 2017. 10. 11.
 * @param lsNmPara
 * @param docType
 * @param txtPara
 * @param lsIds
 * @param isLawNm
 * @param joEfYd
 * @param lsType
 * @param linkLawNm
 * @param linkStr
 * @param joSeq
 * @param linkJoNo
 * @param chkGubun
 */
function fncLawPop(lsNmPara, docType, txtPara, lsIds, isLawNm, joEfYd, lsType, linkLawNm, linkStr, joSeq, linkJoNo, chkGubun) {
	
	linkParamDel();
 	var lsiSeq = getValue("lsiSeq");
	var tempLsNm = lsNmPara.replaceAll("<strong>","");
	tempLsNm = tempLsNm.replaceAll("</strong>",""); // a1 조문링크 구분자 
	tempLsNm = tempLsNm.replace("(구)",""); // (구)w제거
	
	// 법령 연계 관련. if조건 추가. 원래 조건은 else if 로  2014.06.11
	// docType 이 "LO", "LR", "OR"일 때만 팝업창이 뜨도록.
	// 2014.09.25 linkStr 에 '대통령령', '부령'이 들어갈 때도 이쪽을 타도록.
	
	if(!linkStr) {
		linkStr = "";
	}
	
	if ((linkStr.indexOf("대통령령") > -1 || linkStr.indexOf("부령") > -1) && (docType == "")) {
		docType = "JO";  // 특정 법령, 조문이 링크되어 있을때
	}

	if (docType == "LO" || docType == "LR" || docType == "OR") {
			
		//link가 enable 하지 않을때는 팝업창 뜨지 않도록 if절 추가 
		//2014.06.24
		//2014.08.08
		var isEnableLink = true;
		if (!isEnableLink) {
			return;
		} else {
		
			var lsId = lsIds;
			var lsThdCmpCls = docType;
			var joNo = txtPara;
			var url = "lumLsLinkPop.do?" + "lsId=" + lsId + "&lsThdCmpCls=" + lsThdCmpCls
						+ "&joNo=" + joNo + "&linkText=" + linkStr;
	
			var size = "width=798, height=681, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no";
			
			// 팝업창 중복 열림 방지  2014.06.25
			var popObj = window.open(url, 'lsLinkPop', size);
			
			openLinkPop(popObj);
			
			return;
			
		}
	} else if (docType.substring(0,1) == "B") { // 별표서식
		
	    var bylNO = "";
	    var bylBrNo = "";
	    
	    if (txtPara != "") {
	    	 try {
		    	bylNo = txtPara.substring(0,4);
		    	bylBrNo = txtPara.substring(4);
		  	} catch(e){}
	    }
	   
	    if (typeof lsiSeq == null) {
	    	lsiSeq = "";
	    }
	    
	    try {
	    	if (tempLsNm != lsNmPara) {
	    		lsiSeq = "";
	    	}
	    } catch(e){}
	        
	    if (tempLsNm == "영") {
	    	try {
				var lsNmFull = getValue("lsNmTrim");
				
				if (lsNmFull != null) {
					if (lsNmFull.indexOf("시행규칙") > -1) {
						lsNmFull = lsNmFull.substring(0,lsNmFull.indexOf("시행규칙"));
						tempLsNm = lsNmFull + "시행령";
					}
				}
	    	} catch(e){}
	    }
	    
	    if (linkLawNm == "Ordin") {
	    	
	    	 var ordinSeq = getValue("ordinSeq");
	    	 var bylClsNm = "";
	    	 
	    	 if (docType == "BE") {
	    	 	bylClsNm = "별표";
	    	 } else if (docType == "BF") {
	    	 	bylClsNm = "서식";
	    	 } else if (docType == "BG") {
	    		bylClsNm = "별지"; 
	    	 } else if(docType == "BH"){
	    		bylClsNm = "별도"; 
	    	 } else {
	    	 	bylClsNm = "";
	    	 }
	    	 
	    	 if(ordinSeq == "") {
	    		 ordinSeq="0"
	    	 }
	    	 
	    	 openPop("ordinBylInfoPLinkR.do?ordinSeq=" + ordinSeq + "&ordinNm=" + encodeURIComponent(tempLsNm)
						+ "&bylNo=" + bylNo + "&bylBrNo=" + bylBrNo + "&bylClsNm="+ encodeURIComponent(bylClsNm)
						+ "&bylEfYd=" + joEfYd + "&ordinId=" + lsIds);
	    } else if(linkLawNm == "Admrul") {
	    	
	    	 if (docType == "BE") {
	    	 	bylClsNm = "별표";
	    	 } else if (docType == "BF") {
	    	 	bylClsNm = "서식";
	    	 } else if (docType == "BG") {
	    		bylClsNm = "별지"; 
	    	 } else {
	    	 	bylClsNm = "";
	    	 }
	    	 
	    	 openPop("admRulBylInfoPLinkR.do?admRulNm=" + encodeURIComponent(tempLsNm)
						+ "&bylNo=" + bylNo + "&bylBrNo=" + bylBrNo + "&bylClsNm="+ encodeURIComponent(bylClsNm)
						+ "&bylEfYd=" + joEfYd);
	    } else {
		    // lsiSeq long Type
		    if (lsiSeq == "") {
		    	lsiSeq="0"
		    }
			openPop("lsBylInfoPLinkR.do?lsiSeq=" + lsiSeq + "&lsNm=" + encodeURIComponent(tempLsNm)
						+ "&bylNo=" + bylNo + "&bylBrNo=" + bylBrNo
						+ "&bylCls="+docType + "&bylEfYd=" + joEfYd + "&bylEfYdYn=Y");
		}
	    
	} else if (docType == "TL") {
		url = "trtyInfoP.do?trtyNm=" + encodeURIComponent(tempLsNm) + "&chrClsCd=010202&mode=4&lnkYn=Y"
		openPop(url, 1000);
	} else {
		
		// 법령 , 조문
		if (txtPara != "") {
			
			if (joEfYd == '') {
				linkJoNo = '';
			}
			
			if ("법" == lsNmPara && chkGubun == "chkOrdin" ) {
				fSlimUpdateByOrdinJoConLawAjax("lsJoLayer", "ordinLsJoListR.do", "ordinSeq=" + getValue("ordinSeq"),
						tempLsNm, txtPara, docType, lsIds, linkLawNm, linkStr, joEfYd, linkJoNo, chkGubun);
			} else {
				//tempLsNm = encodeURIComponent(tempLsNm);
				joInfoShow(tempLsNm, txtPara, docType, lsIds, linkLawNm, linkStr, joEfYd, linkJoNo, chkGubun);		
			}
			
		} else {
			
			var url = "";
			
			if (linkLawNm == "Ordin") { // 자치법규
				url = "ordinLinkProc.do?" + "ordinNm=" + encodeURIComponent(tempLsNm) 
					+ "&chrClsCd=" + getValue("lsBdyChrCls") + "&mode=20";
				
				if ((lsIds.indexOf("detc") < 0) && (lsIds.indexOf("expc") < 0) && (lsIds.indexOf("decc") < 0)
						&& (lsIds.indexOf("ftc") < 0) && (lsIds.indexOf("acr") < 0) && (lsIds.indexOf("ppc") < 0)) {
					url = url + "&ordinId=" + lsIds;
				}
				
			} else if (linkLawNm == "Admrul") {	// 행정규칙
				url = "admRulLinkProc.do?" + "admRulNm=" + encodeURIComponent(tempLsNm)
					+ "&chrClsCd=" + getValue("lsBdyChrCls") + "&mode=20";
			} else { // 법령
				url = "lsLinkProc.do?" + "lsNm=" + encodeURIComponent(tempLsNm) 
					+ "&joLnkStr=" + encodeURIComponent(linkStr) + "&chrClsCd=" + getValue("lsBdyChrCls");
				
				if ((lsIds.indexOf("detc") > -1) || (lsIds.indexOf("expc") > -1) || (lsIds.indexOf("decc") > -1)) {
					var efYd = lsIds.substring(4, lsIds.length);
					url = url + "&efYd=" + efYd + "&mode=21";
				} else {
					url = url + "&mode=20";
				}
			}
			
			if (el('ancYd') != null && el('ancYd').value != "") {
				if (lsiSeq == null) {
					openPop(url + "&ancYd=" + el('ancYd').value, 1000);
				} else {
					openPop(url,1000);
				}
			} else if (typeof ancYd != 'undefined' && ancYd != "") {
				openPop(url + "&ancYd=" + ancYd, 1000);
			} else {
				openPop(url, 1000);
			}
		}
	}
}

// 법령 lsi_seq 값 가져오기
function getValue(idName){
	try{
		return el(idName).value;	
	}catch(e){
		return "";
	}
}

var linkParam = {lsiSeq : ""
				 ,ancYd : ""
				 ,lsClsCd : ""
				 ,lsNm : ""
				 ,lsId : ""
				 ,chrClsCd : ""
				 ,joNo : ""
			     ,endJoNo : ""
				 ,efYd : ""
				 ,joEfYd : ""
				 ,mode : ""
				 ,ordinSeq : ""
				 ,ordinNm : ""
				 ,ordinId : ""
				 ,joLnkStr : ""
				 ,lnkJoNo : ""
			     ,lnkGubun : ""
				 };

function linkParamDel(){
	linkParam.lsiSeq = "";
	linkParam.ancYd = "";
	linkParam.lsClsCd = "";
	linkParam.lsNm = "";
	linkParam.lsId = "";
	linkParam.chrClsCd = "";
	linkParam.joNo = "";
	linkParam.mode = "";
	linkParam.ordinSeq = "";
	linkParam.ordinNm = "";
	linkParam.ordinId = "";

}

/**
 * <pre>
 * 	법령링크 조문 팝업
 * </pre>
 * @author brKim
 * @since 2017. 10. 11.
 * @param lsNmPara
 * @param joNo
 * @param docType
 * @param lsIds
 * @param linkLawNm
 * @param linkStr
 * @param joEfYd
 * @param linkJoNo
 * @param chkGubun
 */
function joInfoShow(lsNmPara,joNo,docType, lsIds, linkLawNm,linkStr,joEfYd,linkJoNo, chkGubun) {
	
	// 2012.02.15 헌법일경우 임시추가.
	if (lsNmPara == '헌법') {
		lsNmPara = '대한민국헌법';
	}
	
	var lsiSeq  = getValue("lsiSeq");
	var ancYd   = getValue("ancYd");
	var lsClsCd = getValue("lsClsCd");
	var lsNm    = getValue("lsNm");
	var lsId    = getValue("lsId");
	
	linkParam.chrClsCd = getValue("lsBdyChrCls");
	linkParam.joLnkStr = linkStr;
	linkParam.lnkJoNo = linkJoNo;
	
	if (linkStr == undefined) { 
		linkStr = '';
	}
	if (joEfYd == undefined) { 
		joEfYd = '';
	}
	if (linkJoNo == undefined) { 
		linkJoNo = '';
	}
	if (linkLawNm == undefined) { 
		linkLawNm = '';
	}
	
	// 자치법규 처리
	if (linkLawNm != "Ls"
	   && linkLawNm != "Admrul"
	   && lsNmPara.indexOf("대통령령") < 0 && lsNmPara.indexOf("부령") < 0 
	   && lsNmPara.indexOf("총리령") < 0 && lsNmPara.indexOf("대법원규칙") < 0
	   && lsNmPara.indexOf("국회규칙") < 0 && lsNmPara.indexOf("헌법재판소규칙") < 0
	   && lsNmPara.indexOf("중앙선거관리위원회규칙") < 0 && lsNmPara.indexOf("감사원규칙") < 0
	   && lsIds.indexOf("prec") < 0 && lsIds.indexOf("detc") < 0 && lsIds.indexOf("expc") < 0 && lsIds.indexOf("decc") < 0	   
	   && lsIds.indexOf("ftc") < 0 && lsIds.indexOf("acr") < 0 && lsIds.indexOf("ppc") < 0
	   && chkGubun == "chkOrdin") {
		
		lsiSeq  = getValue("ordinSeq");
	    lsNm    = getValue("ordinNm");
	    lsId    = getValue("ordinId");
	    
		if (lsNmPara == "조례") {
		    linkLawNm = "Ordin";
		    linkParam.ordinNm = lsNm;
		    linkParam.ordinId = lsId;
		    linkParam.ordinSeq = lsiSeq;
		} else if (lsNmPara.indexOf("조례") > 0) {
			lsNm = lsNmPara;
			lsNmPara = "조례";
			linkParam.ordinNm = lsNm;
		    linkParam.ordinId = lsId;
		    linkParam.ordinSeq = lsiSeq;
		} else if (lsNmPara == "규정") {
		    linkLawNm = "Ordin";
		    linkParam.ordinNm = lsNm;
		    linkParam.ordinId = lsId;
		    linkParam.ordinSeq = lsiSeq;
		} else if (lsNmPara.indexOf("규정") > 0) {
			lsNm = lsNmPara;
			lsNmPara = "규정";
			linkParam.ordinNm = lsNm;
			linkParam.ordinId = lsId;
			linkParam.ordinSeq = lsiSeq;
		} else if (lsNmPara == "규칙") {
		    linkLawNm = "Ordin";
		    linkParam.ordinNm = lsNm;
		    linkParam.ordinId = lsId;
		    linkParam.ordinSeq = lsiSeq;
		} else if (lsNmPara.indexOf("규칙") > 0) {
			lsNm = lsNmPara;
			lsNmPara = "규칙";
			linkParam.ordinNm = lsNm;
			linkParam.ordinId = lsId;
			linkParam.ordinSeq = lsiSeq;
		} else {
			lsNm = lsNmPara;
			linkParam.ordinNm = lsNm;
			linkParam.ordinId = lsId;
			linkParam.ordinSeq = lsiSeq;
		}
	}
	
	if (lsIds.indexOf("prec") > -1) {
		lsNm = getValue("precNm");
		var precYd = getValue("precYd");
		if (lsIds == "prec") {
			lsIds = lsIds+precYd;
		}
	}
	if (lsIds.indexOf("detc") > -1) {
		lsNm    = getValue("detcNm");
	}
	if (lsIds.indexOf("expc") > -1) {
		lsNm    = getValue("expcNm");
	}

	if (lsIds.indexOf("decc") > -1) {
		lsNm    = getValue("deccNm");
	}
	
	if (lsIds.indexOf("ftc") > -1) {
		lsNm    = getValue("ftcNm");
	}
	
	if (lsIds.indexOf("acr") > -1) {
		lsNm    = getValue("acrNm");
	}
	
	if (lsIds.indexOf("ppc") > -1) {
		lsNm    = getValue("ppcNm");
	}
	
	if (lsId == "" && lsIds != "") {
		lsId = lsIds;
	}

	if (lsNm != "") {
		if (lsNmPara == lsNm) {
			if(linkLawNm == "Admrul"){
				linkParam.admRulNm = lsNmPara;
				linkParam.mode = 100;
			} else {
			linkParam.lsNm = lsNm;
			linkParam.joEfYd = joEfYd;
			linkParam.mode = 2;
			}
			linkParam.lsId = lsId;
			linkParam.joNo = joNo;
		} else if (lsNmPara == "법") {
			lsNm = makeLsLNm(lsClsCd);
			if (lsNm != getValue("lsNmTrim")) {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 3;
				linkParam.lsNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.lsClsCd = lsClsCd + "L";
				linkParam.lsId = lsId;
				logger.def("법 1",1);
			} else {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 3;
				linkParam.lsNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.lsClsCd = lsClsCd + "L";
				linkParam.lsId = lsId;
				linkParam.lsiSeq = lsiSeq;
				logger.def("법 2",1);
			}	
		} else if (lsNmPara == "조례") {
			if (lsNm != getValue("lsNmTrim")) {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 4;
				linkParam.ordinNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.ordinId = lsId;
				logger.def("조례 1",1);
			} else {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 4;
				linkParam.ordinNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.ordinId = lsId;
				linkParam.ordinSeq = lsiSeq;
				logger.def("조례 2",1);
			}	
		} else if (lsNmPara == "규정") {
			if (lsNm != getValue("lsNmTrim")) {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 4;
				linkParam.ordinNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.ordinId = lsId;
				logger.def("규정 1",1);
			} else {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 4;
				linkParam.ordinNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.ordinId = lsId;
				linkParam.ordinSeq = lsiSeq;
				logger.def("규정 2",1);
			}	
		} else if (lsNmPara == "규칙") {
			if (lsNm != getValue("lsNmTrim")) {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 4;
				linkParam.ordinNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.ordinId = lsId;
				logger.def("규칙 1",1);
			} else {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 4;
				linkParam.ordinNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.ordinId = lsId;
				linkParam.ordinSeq = lsiSeq;
				logger.def("규칙 2",1);
			}	
		} else if (lsNmPara == "영") {
			lsNm = makeLsONm(lsClsCd);
			if (lsNm != getValue("lsNmTrim")) {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 3;
				linkParam.lsNm = lsNm;
				linkParam.ancYd = ancYd;
				linkParam.lsClsCd = lsClsCd + "O";
				linkParam.lsId = lsId;
				logger.def("영 1",1);
			} else {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 3;
				linkParam.ancYd = ancYd;
				linkParam.lsClsCd = lsClsCd + "O";
				linkParam.lsId = lsId;
				linkParam.lsiSeq = lsiSeq;
				logger.def("영 2",1);
			}
		} else if ((lsNmPara.indexOf("대통령령") >-1 || lsNmPara.indexOf("대법원규칙") >-1
				|| lsNmPara.indexOf("국회규칙")>-1 || lsNmPara.indexOf("헌법재판소규칙")>-1
				|| lsNmPara.indexOf("중앙선거관리위원회규칙")>-1 || lsNmPara.indexOf("감사원규칙")>-1) && !linkStr) {
			if (lsId == "" && lsIds != "") {
				lsId = lsIds;
			}
			linkParam.joNo = joNo;
			linkParam.joEfYd = joEfYd;
			linkParam.mode = 5;
			linkParam.ancYd = ancYd;
			linkParam.lsClsCd = lsClsCd + "O";
			linkParam.lsId = lsId;
			linkParam.lsiSeq = lsiSeq;
			logger.def("대통령령",1);
		} else if (lsNmPara.indexOf("부령") > -1 || lsNmPara.indexOf("총리령") > -1) {
			if (lsId == "" && lsIds != "") {
				lsId = lsIds;
			}
			linkParam.joNo = joNo;
			linkParam.joEfYd = joEfYd;
			linkParam.mode = 5;
			linkParam.ancYd = ancYd;
			linkParam.lsClsCd = lsClsCd + "R";
			linkParam.lsId = lsId;
			linkParam.lsiSeq = lsiSeq;
			linkParam.lsNm = lsNmPara; // 파라미터명을 전송
			logger.def("부령",1);
		} else if (lsNmPara == "" && lsiSeq != "") {
			linkParam.joNo = joNo;
			linkParam.joEfYd = joEfYd;
			linkParam.mode = 2;
			linkParam.lsId = lsId;
			linkParam.lsiSeq = lsiSeq;
			logger.def("법령명 x ,lsiSeq 있음 ",1);
		} else {
			// 법령명 제 xx 조
			if (lsIds != null && lsIds != "" 
				&& (lsIds.indexOf("prec") > -1  || lsIds.indexOf("detc") > -1)) {
			    linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 11;
				linkParam.lsNm = encodeURIComponent(lsNmPara);
				linkParam.ancYd = ancYd;
				linkParam.lsId = lsId;
				linkParam.efYd = lsIds.substring(4, lsIds.length);
				linkParam.lsClsCd = lsClsCd + "L";
				logger.def("제 xx조",1);
			} else {
				if(lsNmPara.indexOf("조례")>-1){
					linkParam.joNo = joNo;
					linkParam.mode = 16;
					linkParam.ancYd = ancYd;
					linkParam.lsNm = lsNmPara;
					linkParam.lsClsCd = lsClsCd + "R";
					linkParam.lsId = lsId;
					linkParam.lsiSeq = lsiSeq;
					logger.def("조례",1);
				} else {
					linkParam.joNo = joNo;
					linkParam.joEfYd = joEfYd;
					linkParam.mode = 10;
					linkParam.lsNm = lsNmPara;
					linkParam.ancYd = ancYd;
					linkParam.lsId = lsId;
					linkParam.lsClsCd = lsClsCd + "L";
					linkParam.ordinNm = lsNmPara;
					logger.def("제 xx조",1);
				}
			}
		}
	} else {
		
		if(linkLawNm == "Admrul"){
			linkParam.admRulNm = lsNmPara;
			linkParam.lsId = "";
			linkParam.mode = 100;
			linkParam.joNo = joNo;
			linkParam.gubun = "admRul"
		}else{
			// 법령명 제 xx 조 
			if (lsIds != null && lsIds != ""
				&& (lsIds.indexOf("prec") > -1  || lsIds.indexOf("detc") > -1 || lsIds.indexOf("expc") > -1)) {
				linkParam.joNo = joNo;
				linkParam.joEfYd = joEfYd;
				linkParam.mode = 11;
				linkParam.lsNm = lsNmPara;
				linkParam.ancYd = ancYd;
				linkParam.lsId = lsId;
				linkParam.efYd = lsIds.substring(4, lsIds.length);
				linkParam.lsClsCd = lsClsCd + "L";
				logger.def("제 xx조",1);
			} else {
				if(lsNmPara.indexOf("조례")>-1){
					linkParam.joNo = joNo;
					linkParam.mode = 16;
					linkParam.ancYd = ancYd;
					linkParam.lsNm = lsNmPara;
					linkParam.lsClsCd = lsClsCd + "R";
					linkParam.lsId = lsId;
					linkParam.lsiSeq = lsiSeq;
					logger.def("조례",1);
				} else {
					linkParam.joNo = joNo;
					linkParam.joEfYd = joEfYd;
					linkParam.mode = 4;
					linkParam.lsNm = lsNmPara;
					linkParam.ancYd = ancYd;
					linkParam.lsId = lsId;
					linkParam.lsClsCd = lsClsCd + "L";
					logger.def("법령명 x",1);
					linkParam.lsiSeq = lsiSeq;
				}
			}
		}
	}
	logger.def(makeParam(linkParam),1);
	lsJoLayNewView(linkParam, linkLawNm);
}
	// commonLsJs.jsp 에서 이사옴

/**
 * <pre>
 * 	조례-조례 시행규칙 위임링크 팝업
 * </pre>
 * @author yjSeo
 * @since 2023. 09. 21.
 */
function fncOrdinPttnLinkPop(ordinlnkpttnSeq){
	$.ajax({
		method: "POST",
		url: "ordinPttnLinkChk.do",
		dataType:'text',
		data : {ordinlnkpttnSeq : ordinlnkpttnSeq},
		timeout : 10000,
		success:function(data){
			if("jo" == data){
				var url = "ordinLinkPttnPop.do?ordinlnkpttnSeq=" + ordinlnkpttnSeq;
				var size = "width=798, height=681, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no";
				
				//팝업창 중복 열림 방지
				window.open(url, '', size);
			} else if("ne" == data){
				var divId = 'joTempDeleLayer';
				lnkTitle = "<div class=\"towp2\" style=\"width:614px;\"><DIV class=ltit2 style=\"width:550px;\" id=\"tmpLtit2Link\">자치법규</DIV>"
					+"<div class=\"btn22\" style=\"float:right;\">"
					+"<A href=\"#AJAX\" onclick=\"javascript:TempJoDeleLayer.hiddenTempLsLinkLayer();return false;\"><IMG class=maJoHst alt=닫기 src=\"/LSW/images/button/btn_close8.gif\">"
					+"</A></DIV></div>";
				
				$("#"+divId).html("<div class=\"vwrap4\" style=\"left:0px;height:300px; width: 620px;\" id=\"contwrapLinkDiv\">"+
									"<div class=\"viewla11\" style=\"width: 614px; border-top:1px solid #ffffff;margin-top:-6px; height: 110px;\" id=\"viewLinkDiv\">"+
									"<div style=\"width:590px; height:95px; padding:10px 15px; font-family: Gulim,doutm,tahoma,sans-serif; font-size: 1.1em;\">"+
									"<div class=\"insd\" style=\"height:88px;overflow-x:hidden;overflow-y:hidden;margin-top:-1px;margin-left:0px;margin-right:0px;margin-bottom:0px\" id=\"tmpOrdinLinkDiv\">"+
									"<p style=\"float:left;padding:0; margin:15px 0 0 0\"><img src=\"/LSW/images/icon_alert_cirm2.gif\"></p>"+
									"<ul style=\"float:right;width:550px;\">"+
									"<li style=\"line-height:170%; padding: 0 10px 10px 10px;\"><b>조문에서 위임한 사항을 규정한 하위시행규칙이 없습니다.</b>"+
									"<br>* 자세한 사항은 지자체에 문의하시기 바랍니다.</li>"+
									"</ul>"+
									"</div>"+
									"</div>"+
									"</div>"+
									"</div>");
				
				TempJoDeleLayer.showTempLsLinkLayer(0,lnkTitle);
			}
		},
		error : function(x, t, m) {
			if(t == "timeout"){
				alert("사용량이 많아 응답이 지연 있습니다 잠시 후 다시 사용하시기 바랍니다.");
			}
		}
	});
}

/**
 * <pre>
 * 	자치법규 링크 추출 팝업
 * </pre>
 * @author swKim
 * @since 2023. 06. 23.
 */
function fncOrdinLawPop(lsDatId, lsClsCd, gubunCd, stJoNo, stJoDashNo, stJoBrNo,  edJoNo, edJoDashNo, edJoBrNo) {
	
	linkParamDel();
 	var url = "";
 	var lnkGubun = "ordin";
 	linkParam.lnkGubun = lnkGubun;

	if (lsClsCd == "010103") { // 자치법규
		
		if(gubunCd.substring(0,4) == "3004"){
			openPop("ordinBylInfoPLinkR.do?ordinId=" + lsDatId +  "&bylNo=" + stJoNo + "&bylBrNo=" 
					+ stJoBrNo + "&bylClsCd=" + gubunCd + "&lnkGubun=" + lnkGubun);
		} else if(gubunCd == "012601"){
			openPop("ordinLinkProc.do?" + "ordinId=" + lsDatId + "&chrClsCd=" + getValue("lsBdyChrCls") + "&mode=20");		
		} 
		else if (lsDatId != null){
			joLnkShow(lsDatId, lsClsCd, gubunCd, stJoNo, stJoBrNo, edJoNo, edJoBrNo, stJoDashNo, edJoDashNo);								
		} 
	    	 
	} else if(lsClsCd == "010102") {
		if(gubunCd.substring(0,4) == "2002") {
			openPop("admRulBylInfoPLinkR.do?admRulId=" + lsDatId
					+ "&bylNo=" + stJoNo + "&bylBrNo=" + stJoBrNo + "&bylClsCd=" + gubunCd + "&lnkGubun=" + lnkGubun);
		} else if(gubunCd == "012601"){
			openPop("admRulLinkProc.do?" + "admRulId=" + lsDatId + "&chrClsCd=" + getValue("lsBdyChrCls") + "&mode=20" + "&lnkGubun=" + lnkGubun);
		} 
		else if (lsDatId != null){
			joLnkShow(lsDatId, lsClsCd, gubunCd, stJoNo, stJoBrNo, edJoNo, edJoBrNo, stJoDashNo, edJoDashNo);					
		} 
    } else{
    	if (gubunCd.substring(0,4) == "1102") {
    		openPop("lsBylInfoPLinkR.do?lsId=" + lsDatId + "&bylNo=" + stJoNo + "&bylBrNo=" + stJoBrNo + "&bylCls=" + gubunCd + "&lnkGubun=" + lnkGubun);
    	} else if(gubunCd == "012601"){
    		openPop("lsLinkProc.do?" + "lsId=" + lsDatId + "&chrClsCd=" + getValue("lsBdyChrCls") + "&mode=20");
    	} else if (lsDatId != null){
    		joLnkShow(lsDatId, lsClsCd, gubunCd, stJoNo, stJoBrNo, edJoNo, edJoBrNo, stJoDashNo, edJoDashNo);					
    	} 
	}
}

/**
 * <pre>
 * 	자치법규 링크 조문 팝업
 * </pre>
 * @author swKim
 * @since 2023. 06. 23.
 */
function joLnkShow(lsDatId, lsClsCd, gubunCd, stJoNo, stJoBrNo, edJoNo, edJoBrNo, stJoDashNo, edJoDashNo){

	var ordinId    = "";
	var admRulId    = "";
	var lsId = "";
    var lnkGubun = "ordin";
    var joNo = stJoNo + stJoDashNo + stJoBrNo;
    var endJoNo = "";
    
	if(edJoNo){
		endJoNo = edJoNo + edJoDashNo + edJoBrNo;	
	}		
	
	// 자치법규 처리
	if (lsClsCd == "010103") {

	    linkParam.ordinId = lsDatId;
	    linkParam.joNo = joNo;
	    linkParam.endJoNo = endJoNo;
	    linkParam.mode = 4;
	    linkParam.lnkGubun = lnkGubun;
	} else if(lsClsCd == "010102"){ //행정규칙

	    linkParam.admRulId = lsDatId;
	    linkParam.joNo = joNo;
	    linkParam.endJoNo = endJoNo;
		linkParam.mode = 100;
		linkParam.lnkGubun = lnkGubun;
	} else if (lsClsCd == "010101"){ //법령
		
	    linkParam.lsId = lsDatId;
	    linkParam.joNo = joNo;
	    linkParam.endJoNo = endJoNo;
	    linkParam.mode = 4;
	    linkParam.lnkGubun = lnkGubun;
	} 	
	logger.def(makeParam(linkParam),1);
	lsJoLayNewView(linkParam, lsClsCd);
}

/**
 * <pre>
 * 	조문 링크 팝업
 * </pre>
 * @author brKim
 * @since 2017. 10. 11.
 * @param linkParam
 * @param linkLawNm
 */
function lsJoLayNewView(linkParam, linkLawNm) {

	try {
		
		if (linkLawNm == "Ordin" || linkLawNm == "010103") { // 자치법규
		    fSlimUpdateByNewAjax("lsLinkLayer", "ordinLinkProc.do", makeParam(linkParam));
		} else if (linkLawNm == "Admrul" || linkLawNm == "010102"){
			fSlimUpdateByNewAjax("lsLinkLayer", "admRulLinkProc.do", makeParam(linkParam));
		} else {
			// 조문 시행일자 적용시 아래 설정을 풀어주세요.
			linkParam.joEfYd = "";				
		    fSlimUpdateByNewAjax("lsLinkLayer", "lsLinkProc.do", makeParam(linkParam));
		}
		
	} catch(e) {
		logger.err("오류:조문링크 update중..." + e);
	}
	
	lnkTitle = "<div class=\"towp2\" id=\"towp2Link\"><DIV class=ltit2 id=\"ltit2Link\">조문정보 </DIV>"
				+"<div class=btn11 style=\"margin-left:65px;\"><a href=\"#\" onclick=\"javascript:fJoHstAll('"+linkLawNm+"');return false;\" title=\"팝업으로 이동\" style=\"margin-right:4px\"><img alt=전체보기 src=\"/LSW/images/button/btn_view1.gif\"></a>"
				+"&nbsp;<a href=\"#\" onclick=\"javascript:fJoLnkInfoPrint('"+makeParam(linkParam)+"','"+linkParam.mode+"');return false;\" title=\"팝업으로 이동\"><img alt=인쇄 src=\"/LSW/images/button/btn_print3.gif\"></a>" 
				+"</div><div class=\"btn22\" style=\"float:right;\">"
				+"<a href=\"#\" onclick=\"javascript:LsLinkLayer.hiddenLsLinkLayer();return false;\"><img class=maJoHst alt=닫기 src=\"/LSW/images/button/btn_close8.gif\">"
				+"</a></div></div>";
}

// 법령 명이 법일때
function makeLsLNm(lsClsCd){
	var lsNmFull = getValue("lsNmTrim");
	if(lsNmFull != ""){
		if(lsClsCd == 'O'){
			if(lsNmFull.indexOf("시행령") > -1){
				lsNmFull = lsNmFull.substring(0,lsNmFull.indexOf("시행령"));
			}
		}else if(lsClsCd == 'R'){
			if(lsNmFull.indexOf("시행규칙") > -1){
				lsNmFull = lsNmFull.substring(0,lsNmFull.indexOf("시행규칙"));
			}
		}
		return lsNmFull;
	}else{
		return false;
	}
}

// 법령 명이 영일때
function makeLsONm(lsClsCd){
	var lsNmFull = getValue("lsNmTrim");
	if(lsNmFull != null){
		if(lsNmFull.indexOf("시행규칙") > -1){
			lsNmFull = lsNmFull.substring(0,lsNmFull.indexOf("시행규칙"));
			lsNmFull = lsNmFull + "시행령";
		}
		return lsNmFull;
	}else{
		return false;
	}
}

function fSlimUpdateByOrdinJoConLawAjax(divLayId,urlName,parameter,tempLsNm,txtPara,docType, lsIds, linkLawNm,linkStr,joEfYd,linkJoNo, chkGubun){ // fSlimUpdateByAjax 와 같지만 요청 결과 값이 없을때 법령본문 팝업 추가  2012.07.17
Ext.Ajax.request({
   url: urlName,
    scripts: true,
    params: parameter,
    timeout: 3000000,
    success: function(){
		Ext.get(divLayId).dom.innerHTML = arguments[0].responseText;
		tempLsNm = getValue("lsNm1");
		joInfoShow(tempLsNm,txtPara,docType, lsIds, linkLawNm,linkStr,joEfYd,linkJoNo, chkGubun);		
    }
});
}

/**
 * <pre>
 * 	연혁 로딩 및 조회 (연혁 버튼)
 * </pre>
 * @author brKim
 * @since 2017. 6. 12.
 * @param divLayId
 * @param urlName
 * @param parameter
 */
function fSlimUpdate(divLayId, urlName, parameter) {
	
	layoutLoadMask(divLayId);
	// 마스크 작업 후 화면 호출
	$("#"+divLayId).load(urlName, parameter,
			function(response, status, xhr) {
				layoutUnMask(divLayId);
			}
	);
}

/**
 * <pre>
 * 	연혁 버튼 ajax 조회 (현재 조회중인 법)
 * </pre>
 * @author brKim
 * @since 2017. 6. 12.
 * @param divLayId
 * @param urlName
 * @param parameter
 */
function fSlimUpdateByAjax(divLayId, urlName, parameter) {
	
	$.ajax({
		url: urlName
	   ,data: parameter
	   ,dataType: "html"
	   ,timeout: 3000000
	   ,success: function(responseText) {
		   
		   $("#"+divLayId).html(responseText);
		   
		   var thdWidthSize = null;
		   
		   if (divLayId == "joHstLayer") {
			   
			   thdWidthSize = $('#joHstLayer').parent().width();
			   
		   } else if (divLayId == "lsLinkLayer") {
			   
				thdWidthSize = $('#lsLinkLayer').parent().width();
				
			    if ($('#lsLinkTable')) {
			    	$('#lsLinkTable').width(thdWidthSize); // 15
			    }
			    
			} else if (divLayId == "unOrdinLayer") {
				
				unOrdinLayer.showUnOrdinLayer(0, "조례위임조문");
				$('#unOrdinLayer').css('height', $("#lelistwrapLeft").height() - 10);
				$('#vwrap2').css('height', $('#lelistwrapLeft').height() - 10);
				$('#viewlaUnOrdin').css('height', $('#lelistwrapLeft').height() - 10);
				$('#unOrdinDiv').css('height', $("#lelistwrapLeft").height() - 10);
				$('#unOrdinIns').css('height', $("#lelistwrapLeft").height() - 10);
				
			} else if (divLayId == "unOrdinJoHstLayer") {
				
				thdWidthSize = $('#unOrdinJoHstLayer').parent().width();
				
				var layWidth = 0;
				
				if ($('#joHstInfoHong').val() == 1) {
					
					layWidth = 407;
					
					$('#viewLaDiv').css('width', '399px');
					$('#hskhskin0').html("");
					
				} else {
					
					layWidth = 800;
					
					$('#viewLaDiv').css('width', '792px');
				}
				
				var title = "<div class=\"Intmodal_header\" style=\"background: url(images/main/mint_hd_Bg_54.gif) repeat-x 100% 0;width:" + (layWidth-7) + "\">" +
						    	"<div>" +
						    		"<h3 class=\"unOrdinlayerH3\" style=\"width:300px; float:left;\">조문연혁 (공포일기준)</h3>" +
						    	"</div>" +
						    	"<div class=\"btn22\" style=\"float:right; padding:4px 4px 0 0;\">" +
						    		"<a href=\"#AJAX\" onclick=\"javascript:unOrdinJoHstLayer.hiddenUnOrdinJoHstLayer();return false;\">" +
						    			"<img class=maJoHst alt=닫기 src=\"/LSW/images/button/btn_close8.gif\">" +
						    		"</a>" +
						    	"</div>" +
						    "</div>";

				document.getElementById("joHstDiv").scrollLeft = 50000;
				
			} else if (divLayId == "unOrdinReformLayer") {
				
				var listSize = $('#unOrdinReformListSize').val();
				
				if (listSize == 1) {
					
					var goUrl = $('#goUrl').val();
					
					unOrdinReformPop(goUrl);
					
					$('#unOrdinReformDivWrite').html("<div id=\"unOrdinReformLayer\" style=\"display:none\"></div>");
					
				} else {
					
					unOrdinReformLayer.showUnOrdinReformLayer(0,'규제개혁대상법령');
					
				}
			}
		   document.body.style.cursor = "default";
		}
	});
}

/**
 * <pre>
 * 	조례위임조문 레이어 호출
 * </pre>
 * @author brKim
 * @since 2017. 10. 16.
 * @param divLayId
 * @param urlName
 * @param parameter
 * @param urlGubun
 */
function fSlimUnOrdinUpdateByAjax(divLayId,urlName,parameter, urlGubun) {
	
	$.ajax({
		url: urlName
	   ,data: parameter
	   ,timeout: 3000000
	   ,success: function(responseText) {
			$('#'+divLayId).html(responseText);
			
			if (urlGubun == 'lsSc') {
				$("#unOrdinLayer").css("height", $("#lelistwrapLeft").height() - 10);
				$("#vwrap2").css("height", $("#lelistwrapLeft").height() - 10);
				$("#viewlaUnOrdin").css("height", $("#lelistwrapLeft").height() - 10);
				$("#unOrdinDiv").css("height", $("#lelistwrapLeft").height() - 10);
				$("#unOrdinIns").css("height", $("#lelistwrapLeft").height() - 10);
				unOrdinLayer.showUnOrdinLayer(0, "조례위임조문", 1);
			} else {
				unOrdinLayer.showUnOrdinLayer(0, "조례위임조문", 2);
			}
	   }
	});
	
}

/**
 * <pre>
 * 	연혁 버튼 ajax 조회 (현재 조회중인 법의 이전법들)
 * </pre>
 * @author brKim
 * @since 2017. 6. 12.
 * @param divLayId
 * @param urlName
 * @param parameter
 * @param no
 */
function fSlimUpdateByAjaxDiff(divLayId, urlName, parameter, no) {
	layoutLoadMask(divLayId);
	
	$.ajax({
		url: urlName
	   ,data: parameter
	   ,dataType: "html"
	   ,type:'POST'
	   ,timeout: 3000000
	   ,success: function(responseText) {
		   var diffVal = responseText;
		   var diffCut = diffVal.split("diffCut");
		   
		   eval(el("hhhong3"+no)).innerHTML = diffCut[0];
		   eval(el("hhhong1"+(no-1))).style.display = "none";
		   eval(el("hhhong3"+(no))).style.display = "none";
		   if(eval(el("hhhong3"+(no))).style.display == "none"){
			   eval(el("hhhong3"+(no))).style.display = "";
		   }

		   eval(el("hhhong2"+no)).innerHTML = diffCut[1];
		   eval(el("hhhong1"+no)).style.display = "none";
		   eval(el("hhhong2"+(no))).style.display = "none";
		   if(eval(el("hhhong2"+no)).style.display == "none"){
			   eval(el("hhhong2"+(no))).style.display = "";
		   }
		   
		   eval(el("hhhong2"+(no-1))).style.display = "none";
		   eval(el("hhhong3"+(no-1))).style.display = "none";
		   eval(el("hhhong1"+(no-2))).style.display = "";

		   document.body.style.cursor = "default";
		   
		   layoutUnMask(divLayId);
	   }
	});
}

/**
 * <pre>
 * 	조문 링크 팝업 (신규)
 *  -> fSlimUpdateByAjax 와 같지만 요청 결과 값이 없을때 법령본문 팝업 추가  2012.07.17
 * </pre>
 * @author brKim
 * @since 2017. 10. 11.
 * @param divLayId
 * @param urlName
 * @param parameter
 */
function fSlimUpdateByNewAjax(divLayId,urlName,parameter) {
	
	
	if (urlName == "lsLinkProc.do") {
		
		//var ran = Math.floor(Math.random() * 100) + 1 ; //20170909  추가(화면분리 때문 추가)
		var url = "lsLinkProc.do?" + parameter;
		if($openPopWidth == null || $openPopWidth == "" && $openPopHeight == null || $openPopHeight == ""){
			var popupX = (window.screen.width / 2) - (800 / 2);
			var popupY = (window.screen.height / 2) - (270 / 2);
			var win = window.open(url,'조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=800px,height=266px,left=' + popupX + ',top=' + popupY);
			return false;
		}else{
			var popupX = (window.screen.width / 2) - ($openPopWidth / 2);
			var popupY = (window.screen.height / 2) - ($openPopHeight / 2);
			var win = window.open(url, '조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=' + $openPopWidth + ',height=' + $openPopHeight + ',left=' + popupX + ',top=' + popupY);
			return false;
		}
	}else if(urlName == "ordinLinkProc.do") {
		
		var url = "ordinLinkProc.do?" + parameter;
		if($openPopWidth == null || $openPopWidth == "" && $openPopHeight == null || $openPopHeight == ""){
			var popupX = (window.screen.width / 2) - (800 / 2);
			var popupY = (window.screen.height / 2) - (270 / 2);
			var win = window.open(url,'조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=800px,height=266px,left=' + popupX + ',top=' + popupY);
			return false;
		}else{
			var popupX = (window.screen.width / 2) - ($openPopWidth / 2);
			var popupY = (window.screen.height / 2) - ($openPopHeight / 2);
			var win = window.open(url, '조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=' + $openPopWidth + ',height=' + $openPopHeight + ',left=' + popupX + ',top=' + popupY);
			return false;
		}
	}else if(urlName== "admRulLinkProc.do"){
		
		var url = "admRulLinkProc.do?" + parameter;
		if($openPopWidth == null || $openPopWidth == "" && $openPopHeight == null || $openPopHeight == ""){
			var popupX = (window.screen.width / 2) - (800 / 2);
			var popupY = (window.screen.height / 2) - (270 / 2);
			var win = window.open(url,'조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=800px,height=266px,left=' + popupX + ',top=' + popupY);
			return false;
		}else{
			var popupX = (window.screen.width / 2) - ($openPopWidth / 2);
			var popupY = (window.screen.height / 2) - ($openPopHeight / 2);
			var win = window.open(url, '조문정보', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,menubar=no,width=' + $openPopWidth + ',height=' + $openPopHeight + ',left=' + popupX + ',top=' + popupY);
			return false;
		}		
	}else{
		$.ajax({
			url: urlName
		   ,data: encodeURI(parameter)
		   ,timeout: 3000000
		   ,success: function(responseText) {
			   $("#"+divLayId).html(responseText);
			   if (responseText.length < 1000 && el('lnkLsNm') != null) {

				   // 법령만 적용, lnkLsNm 값을 법령(lsLink.jsp)만 설정
				   // 법령외 적용시 lnkLsNm 값을 설정해주면 됨.
				   // 조문정보가 없는 경우 법령정보 팝업을 호출한다.		
				   var lnkLsNm = getValue('lnkLsNm');
				   var lnkLsiSeq = getValue('lnkLsiSeq');
				   var lnkLsId = getValue('lnkLsId');
				   
				   if (lnkLsNm != "") {
					   var url = "lsLinkProc.do?" + "lsNm=" + encodeURIComponent(lnkLsNm) 
					   			+ "&joLnkStr=" + "&chrClsCd=" + linkParam.chrClsCd + "&mode=20";
					   openPop(url, 1000);
				   } else {
					   LsLinkLayer.showLsLinkLayer(0,lnkTitle);
				   }
				   
			   } else {
				   
				   if (divLayId=="joHstLayer") {
					   var thdWidthSize = $('#joHstLayer').parent().width();
				   }
				   
				   LsLinkLayer.showLsLinkLayer(0,lnkTitle);
				   
				   if (divLayId == "lsLinkLayer" && urlName == "ordinLinkProc.do") {
			   			$("#towp2Link").css("margin-top","-30px");
			   		}
				}
		   }
		});
	}
}

	

/**
 * <pre>
 * 	조문 링크 인쇄
 * </pre>
 * @author brKim
 * @since 2017. 10. 11.
 * @param para
 * @param mode
 */
function fJoLnkInfoPrint(para,mode) {
	
    var para = para;
    var url = "";
    
    if (!para) {
    	para = document.location.href.split("?").pop();
    	para = decodeURIComponent(para);
    }
    
	if (mode == 10) {
		var lsId = getValue("lnkLsId");
		url = "lsLinkProc.do?"+para+"&lsId="+lsId+"&print=print";
		
		if (para.indexOf("lsJoLnkSeq") > -1) {
			url = "lsLawLinkInfo.do?"+para+"&lsId="+lsId+"&print=print";
		} else if (para.indexOf("lsId=") > -1) {
			url = "lsLinkProc.do?"+para+"&print=print";
		}
	} else if (mode == 100) {
		url = "admRulLinkProc.do?"+para+"&print=print";
	} else if (mode == 2) {
		para = decodeURIComponent(para);
		url = "ordinLinkProc.do?"+para+"&print=print";
	}else {
		url = "lsLinkProc.do?"+para+"&print=print";
	}
	
	openPrintPop(url,"조문정보출력");
}

function fncArLawPop(lsNm, ancYd, ancNo){
	var para = "&lsNm=" + encodeURIComponent(lsNm)
	          +"&ancYd=" + ancYd
	          +"&chrClsCd=010202&urlMode=lsRvsDocInfoR"
	          +"&ancNo=" + ancNo;
	var url = "lsSideInfoP.do?"+ para;
	openPop(url);
}


function fncArOrdinPop(ordinNm, ancYd, ancNo){
	var url = "ordinSideInfoP.do?ordinNm=" + encodeURIComponent(ordinNm) + "&ancYd=" + ancYd +"&ancNo="+ancNo + "&urlMode=ordinRvsDocInfoR&chrClsCd=010202";
	openPop(url);
}

/**
 * 조문정보 - 법령보기
 * <shcho> 시행일/공포 서비스개선 : 시행,연혁(ancYnChk: 0=시행, 1=공포) 파라미터 추가
 */
function fJoHstAll(linkLawNm){
	
	var url = "";
	if(linkLawNm == "Ordin") {
		url = "ordinInfoP.do?ordinSeq="+ el('lnkOrdinSeq').value;
	}else {
		url = "lsInfoP.do?lsiSeq="+ el('lnkLsiSeq').value +"&ancYnChk=" + el("ancYnChk").value;
	}
	
	openPop(url);
}

//조문체계도 팝업

function joStmdPop(lsiSeq, joNo, joBrNo){
    var url = "joStmdInfoP.do?lsiSeq=" + lsiSeq + "&joNo=" + joNo + "&joBrNo=" + joBrNo; 

	openScrollPop(url,"1024px");
}


//법령체계도 팝업
/*
* 2019.08.23 <shcho> 시행일/공포 서비스개선 : 시행,연혁(ancYnChk: 0=시행, 1=공포) 파라미터 추가 *
	 * - 상세변경내역 : + "&ancYnChk=" +ancYnChk; 추가
*/
function lsStmdPop(lsiSeq, ancYnChk) {
	
	if(lsiSeq == '' && el("lsiSeq")){
		lsiSeq = el("lsiSeq").value;
	}
	
	if(ancYnChk == '' && el("ancYnChk")) {
		ancYnChk = el("ancYnChk").value;
	}
	
	if (el("lsiSeq")) {
		var url = "lsStmdInfoP.do?lsiSeq=" + lsiSeq + "&ancYnChk=" +ancYnChk; 
		openScrollPop(url, "1024px");
	} else {
		alert(lsVO.msg);
	}
}

// 판례체계도 팝업
function precStmdPop(precSeq){
	var url = "precStmdInfoP.do?precSeq=" + precSeq; 

	openScrollPop(url, "1024px");
}

// 헌재결정례체계도 팝업
function detcStmdPop(detcSeq){
	var url = "detcStmdInfoP.do?detcSeq=" + detcSeq; 
	
	openScrollPop(url, "1024px");
}

// 해석례체계도 팝업
function expcStmdPop(expcSeq){
	var url = "expcStmdInfoP.do?expcSeq=" + expcSeq; 
	
	openScrollPop(url, "1024px");
}

function cgmExpcStmdPop(cgmExpcDatSeq){
	console.log('ls ls link');
	if (cgmExpcDatSeq == '' || cgmExpcDatSeq == 0) {
		alert('본문을 선택하십시요.');
		return;
	}

	console.log('cgm expc seq', cgmExpcDatSeq);
	var url = "cgmExpcStmdInfoP.do?cgmExpcDatSeq=" + cgmExpcDatSeq;

	openScrollPop(url, "1024px");
}

// 심판례체계도 팝업
function deccStmdPop(deccSeq){
	var url = "deccStmdInfoP.do?deccSeq=" + deccSeq; 
	
	openScrollPop(url, "1024px");
}

// 심판례체계도 팝업
function specialDeccStmdPop(deccSeq, trbClsCd){
	if (deccSeq == '' || deccSeq == 0) {
		alert('본문을 선택하십시요.');
		return;
	}
	var url = "specialDeccStmdInfoP.do?specialDeccSeq=" + deccSeq + "&trbClsCd=" + trbClsCd;

	openScrollPop(url, "1024px");
}

//법령체계도 팝업(기타[제개정문] 화면에서 호출할때)
function lsStmdEtcPop(lsiSeq, prcDv){
	var url = "lsStmdInfoP.do?lsiSeq=" + lsiSeq + "&prcDv=" + prcDv;

	openScrollPop(url, "1024px");
}
//법령연계 상세보기   2014.06.10    
 //2014.08.08 상세보기 버튼 없어짐
/*
var isEnableLink = false;

function enableLink(){
	if(isEnableLink){
		$("a[name='detailLink']").each(function(){
			$(this).attr('class', 'disableLink');
			$(this).attr('title', '');
		});
		isEnableLink = false;
	} else {
		$("a[name='detailLink']").each(function(){
			$(this).attr('class', 'enableLink');
			$(this).attr('title', '팝업으로 이동');
		});
		isEnableLink = true;
	}
}
*/
//법령연계 팝업창 중복 열림 방지 2014.06.25
var childWin = null;

function openLinkPop(popObj){
	if(childWin){
	//alert("이미 팝업창이 열려 있습니다.");
		childWin.focus();
	}else{
		childWin = popObj;
	}
	return childWin;
}

// 2014.10.08 위임법령팝업창
function devLawPop(type, lsiSeq, joNo, joBrNo, lnkText){
	var datClsCd = "";
	
	if(type == 'ordin'){
		datClsCd = "010103";
		
		
	}else if(type == 'admrul'){
		datClsCd = "010102";
		
	}else if(type == 'excuAdmrul'){
		datClsCd = "010102";
	}
	var action = "";
	if('010102' == datClsCd){
		if(type == 'admrul'){
			action = "conAdmrulByLsPop.do?";			
		}else if(type == 'excuAdmrul'){
			action = "conExcuAdmrulByLsPop.do?";
		}
	} else {
		action = "lumLsDevPop.do?";
	}
	
	var url = action
	+ "lsiSeq=" + lsiSeq
	+ "&datClsCd=" + datClsCd;
	
	if(typeof joNo != 'undefined'){
		url = url + "&joNo=" + joNo;
		if(typeof joBrNo != 'undefined'){
			url = url + "&joBrNo=" + joBrNo
		}
	}
	
	if(typeof lnkText != 'undefined'){
		url = url + "&lnkText=" + lnkText;
	}

//	var size = "width=798, height=681, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no, scrollbars=yes";
	var size = "width=1024, height=630, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=yes, resizable=yes";
	
	//window.open(url, '', size);
	
	//팝업창 중복 열림 방지  2014.06.25
     var popObj = window.open(url, 'lsDevPop', size);
	//var popObj = window.open(url, 'lsDevPop');
	openLinkPop(popObj);
	
	
	return;

}


/* 자바스크립트에서는 오버로딩을 지원하지 않으므로 항상 아래의 메서드가 동작함 주석 처리
 * 법령에서 위임된 행정규칙 ,위임 자치법규의 조문전체 또는 문자열 링크를 위한 function   
function joDelegatePop(lsiSeq, joNo, joBrNo, datClsCd, lnkText){
	var size = "width=798, height=681, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no, scrollbars=yes";
	//var size = "width=1024, height=630, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=yes, resizable=yes";
	var action = "";
	if('010102' == datClsCd){
		action = "conAdmrulByLsPop.do?";
	} 
//	else {
//		action = "lumLsDevPop.do?";
//	}
	var url = action
		+ "&lsiSeq=" + lsiSeq
		+ "&joNo=" + joNo
		+ "&joBrNo=" + joBrNo
		+ "&datClsCd=" + datClsCd;

	if(typeof lnkText != 'undefined'){
		if('010102' == datClsCd){
			url = url + "&lnkText=" + lnkText;
		}
	}
	
	var popObj = window.open(url, 'lsDevPop', size);
	openLinkPop(popObj);
}	*/

var joDele = {lsiSeq : ""
	 ,joNo : ""
	 ,joBrNo : ""
	 ,datClsCd : ""
	 ,dguBun : ""};


var joDeleGateParam = {lsiSeq : ""
	,joNo : ""
	,joBrNo : ""
	,datClsCd : ""
	,dguBun : ""
};

/* 법령에서 위임된 행정규칙 ,위임 자치법규, 위임 규정의 조문전체 또는 문자열 링크를 위한 function */
function joDelegatePop(lsiSeq, joNo, joBrNo, datClsCd, dguBun, lnkText, pttnSeq){

	if ('NOT' == dguBun) {
		var size = "width=710, height=230, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=no, resizable=yes";
	} else {
		var size = "width=1040, height=630, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=yes, resizable=yes";
		
		if (typeof lnkText == 'undefined') {
			dguBun = "DEG";
		}
	}
	
	var action = "";
	joDele.lsiSeq = lsiSeq;
	joDele.joNo = joNo;
	joDele.joBrNo = joBrNo;
	joDele.datClsCd = datClsCd;
	joDele.dguBun = dguBun;

	if ('010102' == datClsCd) {
		action = "conAdmrulByLsPop.do";
	}else if ('010113' == datClsCd) {
		action = "conSchlPubRulByLsPop.do";
	}
	
	var url = action
		+ "?&lsiSeq=" + lsiSeq
		+ "&joNo=" + joNo
		+ "&joBrNo=" + joBrNo
		+ "&datClsCd=" + datClsCd
		+ "&dguBun=" + dguBun;

	if (typeof lnkText != 'undefined') {
		if ('010102' == datClsCd || '010113' == datClsCd) {
			url = url + "&lnkText=" + encodeURI(encodeURIComponent(lnkText));
		}
	}
	
	// [2017국법개발] pttnSeq 적용 Start
	if(typeof pttnSeq != 'undefined'){
		if('DEG' == dguBun) {
			if ('010102' == datClsCd) {
				url = url + "&admRulPttninfSeq=" + pttnSeq;
			}else if ('010113' == datClsCd) {
				url = url + "&schlPubRulPttninfSeq=" + pttnSeq;
			}
		}
	}
	// [2017국법개발] pttnSeq 적용 End
	
	if ('NOT' == dguBun) {
		lnkTitle = "<div class=\"towp2\" style=\"width:614px;\"><DIV class=ltit2 style=\"width:550px;\" id=\"ltit2Link\">행정규칙</DIV>"
			+"<div class=\"btn22\" style=\"float:right;\">"
			+"<A href=\"#AJAX\" onclick=\"javascript:JoDeleLayer.hiddenLsLinkLayer();return false;\"><IMG class=maJoHst alt=닫기 src=\"/LSW/images/button/btn_close8.gif\">"
			+"</A></DIV></div>";
		joDelegateAjax(action, makeParam(joDele));
	} else {
		var popObj = window.open(url, 'lsDevPop', size);
		openLinkPop(popObj);
	}
}

/*법령에서 위임자치법규 팝업*/
function joDelegateOrdinPop(lsiSeq, lsId, joNo, joBrNo, datClsCd, dguBun, lnkText){
	
	var size = "width=" + screen.width + ", height=700, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=no, resizable=yes,top=1,left=1";
	if(typeof lnkText == 'undefined') dguBun = "DEG";
	
	var action = "";
	joDele.lsiSeq = lsiSeq;
	joDele.joNo = joNo;
	joDele.joBrNo = joBrNo;
	joDele.datClsCd = datClsCd;
	joDele.dguBun = dguBun;
	
	action = "lumThdCmpJo.do";
		
	var url = action
		+ "?lsiSeq=" + lsiSeq
		+ "&joNo=" + joNo
		+ "&joBrNo=" + joBrNo
		+ "&datClsCd=" + datClsCd
		+ "&dguBun=" + dguBun;

	lnkText = lnkText.replaceAll("·", ".");
	lnkText = lnkText.replaceAll("ㆍ", ".");
	
	if(typeof lnkText != 'undefined'){
		url = url + "&lsId=" + lsId + "&chrClsCd=010202&gubun=STD&lnkText=" + encodeURI(encodeURIComponent(lnkText));
	}
		var popObj = window.open(url, 'lsDevOrdinPop2', size);
		openLinkPop(popObj);
}

/*법령에서 관련조례*/
function joDelegateLsPop(lsiSeq, lsId){
	
	if(lsiSeq == '' && el("lsiSeq")){
		lsiSeq = el("lsiSeq").value;
	}
	
	var size = "width=" + screen.width + ", height=700, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no, scrollbars=yes,top=1,left=1";
			
	var action = "lumThdCmpJo.do?";
	var param = "lsiSeq=" + lsiSeq + "&joNo=&joBrNo=&datClsCd=010103&LsAll=Y&chrClsCd=010202&gubun=STD"; 
	var url = action + param;
	
	var popObj = window.open(url, 'lsDevPop2', size);
	openLinkPop(popObj);
	popObj.focus(); 
}

/* 조례 위임조문 레이어 */
var unOrdinLayer = (function() {
	var unOrdinLayer = null;
	return {
		showUnOrdinLayer : function(size, title, gubun) {
			
				//var title = '<div><img src="/LSW/images/cssimg/tab99.gif" alt="자치법규 위임 근거 조문" title="자치법규 위임 근거 조문"/><span style="float: right;">X</span></div>';
				var title =	'<div class="vwrap_tit">'
		    		+	'<h5 class="vw_s_tit"><span>자치법규 위임 근거 조문</span></h5>'
		    		+	'<a href="#" onclick="unOrdinLayer.hiddenUnOrdinLayer();" class="btn_vw_clse">닫기</a>'
		    		+'</div>';
				
				if (!unOrdinLayer) {
				
					unOrdinLayer = $("#unOrdinLayerBtn").dialog({
						autoOpen : false
						   ,modal : false
						   ,resizable: false
						   ,width: '250px'
						   ,title : title
						   ,position : {
								// 내 객체 위치
								my : 'left top',
								// 참조할 객체 위치
								at : 'left top',
								// 참조할 객체 지정
								of : $('#leftContent')
						   }
					});
				
				}
				unOrdinLayer.dialog("open");			
		}
		,hiddenUnOrdinLayer : function(){		
			if (unOrdinLayer) {
				$("#unOrdinLayerBtn").empty();
				unOrdinLayer.dialog("close");
			}
		}
	};
})();


var unOrdinJoHstLayer = function(){
	var unOrdinJoHstLayer;
	return {
		showUnOrdinJoHstLayer : function(size, title, layWidth){
			if(size==0){
					if(unOrdinJoHstLayer){
						unOrdinJoHstLayer.hide();
					}
					title = title.replace("조문정보", "조문연혁");
					unOrdinJoHstLayer = $("#unOrdinJoHstLayer").dialog({
						autoScroll:false
						,title: title
						,width:layWidth  // 800
						,height:450 // 450
						,modal : false
						,resizable : false
						,position : {
							// 내 객체 위치
							my : 'center',
							// 참조할 객체 위치
							at : 'center',
							// 참조할 객체 지정
							of : 'body'
						}
						
				});
					
				// 타이틀 바 숨김
			    //unOrdinJoHstLayer.parent().find('.ui-dialog-titlebar').hide();
				unOrdinJoHstLayer.dialog("open");
 			}
			
			if(size!=0){
				if(size<100){
					win5.setHeight(size+120);
				}else if(size>100 && size < 220){
					win5.setHeight(size+80);
				}		
			}
		}
		,hiddenUnOrdinJoHstLayer : function(){
			if(unOrdinJoHstLayer){
				unOrdinJoHstLayer.dialog('close');
			}
		}
	};
}();

/**
 * <pre>
 * 	위임행정규칙 팝업 레이어
 * </pre>
 * @author brKim
 * @since 2017. 11. 27.
 */
var JoDeleLayer = function() {
	
	var joDeleLayer = null;
	
	return {
		showLsLinkLayer : function(size, title) {
			
			if (size == 0) {
				
				if (joDeleLayer) {
					joDeleLayer.dialog("close");
				}
				
				$('#lsLinkLayer').show();
				
				joDeleLayer = $('#lsLinkLayer').dialog({
	            	autoOpen : false
	               ,width: 620
	               ,height: 145
	               ,modal: false
				   ,title: title
				   ,resizable: false
				   ,position: {
						// 내 객체 위치
						my : 'center',
						// 참조할 객체 위치
						at : 'center',
						// 참조할 객체 지정
						of : 'body'
					}
	            });
				
				joDeleLayer.dialog("open");
			}
		}
		,hiddenLsLinkLayer: function() {
			if (joDeleLayer) {
				joDeleLayer.dialog("close");	
			}
		}
	};
}();
//규제개혁 대상법령
var unOrdinReformLayer = function(){
	var unOrdinReformLayer;
	return {
		showUnOrdinReformLayer : function(size, title){
			if(size==0){
				if(unOrdinReformLayer){
					unOrdinReformLayer.hide();
				}

				Ext.get('unOrdinReformLayer').show();
				
				unOrdinReformLayer = new Ext.Window({
//					title:'<img src="/images/cssimg/tab99.gif" alt="자치법규 위임 근거 조문" title="자치법규 위임 근거 조문"/>'
					title:'<img src="/images/intpop/tab100.gif" alt="규제개혁 대상법령" title="규제개혁 대상법령"/>'
					,width:275
					,height:390
					,closable: true
					,closeAction:'close'
					,autoScroll:false
					,layout: {
				        type: 'fit',
				        align: 'center'
				    }
				    ,defaults: {
				        bodyPadding: 0
				    }
				    ,resizable: false
					,contentEl : 'unOrdinReformLayer'
					,baseCls:'o-window'
					,cls:'owindow'
					,border: false
					,listeners:{'resize':function(){
			           }
    				   ,'close':function(){
    				       el("unOrdinReformDivWrite").innerHTML = "<div id=\"unOrdinReformLayer\" style=\"display:none\"></div>";
    		           }
					}
			    });
				unOrdinReformLayer.show();
			}
		}
		,hiddenUnOrdinReformLayer : function(){
			if(unOrdinReformLayer){
				unOrdinReformLayer.close();			
			}
		}
	};
}();

function joDelegateAjax(urlName,parameter) {
	
	var divId = 'lsLinkLayer';
	
	$.ajax({
		url: urlName
	   ,data : parameter
       ,timeout: 3000000
       ,dataType: "html"
       ,method: "POST"
       ,success: function(responseText){
    	   $('#'+divId).html(responseText);
    	   JoDeleLayer.showLsLinkLayer(0, lnkTitle);
       	}
	});
}

/**
 * <pre>
 * 	법령 본문의 위임행정규칙 목록을 보여준다.
 * </pre>
 * @author brKim
 * @since 2017. 9. 26.
 * @param htmlId
 * @param pLsiSeq
 * @param pJoNo
 * @param pJoBrNo
 * @param pDatClsCd
 * @param pCptYn
 */
function viewDelegatedAdmRul(htmlId, pLsiSeq, pJoNo, pJoBrNo, pDatClsCd, pCptYn) {
	
	var urlName = webRoot + "/lsiJoDelegatedAdmRul.do";
	var parameter = "lsiSeq=" + pLsiSeq
		+ "&joNo=" + pJoNo
		+ "&joBrNo=" + pJoBrNo
		+ "&datClsCd=" + '010102';

	if (!$('#delegated_' + htmlId).html() || !$.trim($('#delegated_' + htmlId).html())) {
		
		$.ajax({
			    url:		urlName
			   ,data:		parameter
			   ,timeout:	3000000
			   ,dataType:	'html'
			   ,success:	function(responseText) {
		        	$('#delegated_' + htmlId).html(responseText);
		        	$("#delegated_"+htmlId).css("display", "block");
		        	$("#delegatedAdmRul_img_"+htmlId).attr("src", webRoot + "/images/common/btn_rule_close.gif");
				}
		});
		
	} else {
		
		if ($("#delegated_"+htmlId).css("display") == "none") {
			$("#delegated_"+htmlId).css("display", "block");
			$("#delegatedAdmRul_img_"+htmlId).attr("src", webRoot + "/images/common/btn_rule_close.gif");
		} else {
			$("#delegated_"+htmlId).css("display", "none");
			$("#delegatedAdmRul_img_"+htmlId).attr("src", webRoot + "/images/common/btn_rule_view.gif");
		}
		
	}
}

/*위임자치법규 테스트*/
function devLawPopTest(type, lsiSeq, joNo, joBrNo, lnkText){
	var datClsCd = "";
	
	if(type == 'ordin'){
		datClsCd = "010103";
	}	
		
	action = "unOrdinListTest.do?";
	
	var url = action
	+ "lsiSeq=" + lsiSeq
	+ "&datClsCd=" + datClsCd;
	
	if(typeof joNo != 'undefined'){
		url = url + "&joNo=" + joNo;
		if(typeof joBrNo != 'undefined'){
			url = url + "&joBrNo=" + joBrNo
		}
	}
	
	if(typeof lnkText != 'undefined'){
		url = url + "&lnkText=" + lnkText;
	}

//	var size = "width=798, height=681, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no, scrollbars=yes";
	var size = "width=722, height=630, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=yes, resizable=yes";
	
	//window.open(url, '', size);
	
	//팝업창 중복 열림 방지  2014.06.25
     var popObj = window.open(url, 'lsDevPop', size);
	//var popObj = window.open(url, 'lsDevPop');
	openLinkPop(popObj);
	
	
	return;

}

function joDelegatePopUnordin(lsiSeq, joNo, joBrNo, datClsCd, dguBun, lnkText){
//	alert(dguBun);
	
	//var size = "width=798, height=681, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no, scrollbars=yes";
	if('NOT' == dguBun){
		var size = "width=710, height=230, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=no, resizable=yes";
	}else{
		var size = "width=1024, height=630, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=yes, resizable=yes";
		
		if(typeof lnkText == 'undefined') dguBun = "DEG"
	}
	var action = "";
	joDele.lsiSeq = lsiSeq;
	joDele.joNo = joNo;
	joDele.joBrNo = joBrNo;
	joDele.datClsCd = datClsCd;
	joDele.dguBun = dguBun;
	action = "unOrdinLnk.do";
	
	var url = action
		+ "?&lsiSeq=" + lsiSeq
		+ "&joNo=" + joNo
		+ "&joBrNo=" + joBrNo
		+ "&datClsCd=" + datClsCd
		+ "&dguBun=" + dguBun;

	if(typeof lnkText != 'undefined'){
		if('010102' == datClsCd){
			url = url + "&lnkText=" + encodeURI(encodeURIComponent(lnkText));
		}
	}
	if('NOT' == dguBun){
		lnkTitle = "<div class=\"towp2\" style=\"width:614px;\"><DIV class=ltit2 style=\"width:550px;\" id=\"ltit2Link\">행정규칙</DIV>"
			+"<div class=\"btn22\" style=\"float:right;\">"
			+"<A href=\"#AJAX\" onclick=\"javascript:JoDeleLayer.hiddenLsLinkLayer();return false;\"><IMG class=maJoHst alt=닫기 src=\"/LSW/images/button/btn_close8.gif\">"
			+"</A></DIV></div>";
		joDelegateAjax(action,makeParam(joDele));
	}else{
		var popObj = window.open(url, 'unOrdinLnkPop', size);
		openLinkPop(popObj);
	}
}	

function unOrdinLsPop(gubun, lsiSeq) {
	
	action = "unOrdinLsList.do";
	var size = "width=528, height=613, scrollbars=no, toolbar=no, resizable=yes, status=no, location=yes, menubar=no, scrollbars=yes, resizable=yes";
	var url = action
		+ "?&lsiSeq=" + lsiSeq;
	var popObj = window.open(url, 'unordinLsPop', size);
	openLinkPop(popObj);
}

/**
 * <pre>
 * 	관련규제 목록 Layer 생성
 * </pre>
 * @author brKim
 * @since 2017. 10. 18.
 */
var ctlInfLayer = function() {
	
    var ctlInfLayer = null;
    
    return {
    	
    	showCtlInfLayer : function() {
    		
    		if (ctlInfLayer) {
                ctlInfLayer.dialog("close");
            }
    		
    		if (!ctlInfLayer) {
    			
    			var title =	'<div class="vwrap_tit">'
		    				+	'<h5 class="vw_s_tit"><span>규제사무명</span></h5>'
		    				+	'<a href="#" onclick="ctlInfLayer.hiddenCtlInfLayer();" class="btn_vw_clse">닫기</a>'
		    				+'</div>';
    			
    			ctlInfLayer = $('#ctlInfLayer').dialog({
    				autoOpen: false
    				,width: 250
    				,height: 350
    				,modal: false
    				,title: title
    				,resizable: false
    				,position: {
    					// 내 객체 위치
    					my : 'left top',
    					// 참조할 객체 위치
    					at : 'left top',
    					// 참조할 객체 지정
    					of : $('#leftContent')
    				}
    			});
    		}
    		
    		ctlInfLayer.dialog("open");
        }
        ,hiddenCtlInfLayer : function(){
            if (ctlInfLayer) {
                ctlInfLayer.dialog("close");
            }
        }
    };
}();

/**
 * <pre>
 * 	규제 팝업 (조문 앞 규 버튼)
 * </pre>
 * @author brKim
 * @since 2017. 10. 18.
 * @param lsiSeq
 * @param lsId
 * @param joNo
 * @param joBrNo
 */
function openCtlInfoList(lsiSeq, lsId, joNo, joBrNo) {
	
    var urlName = "lsCtlInfListR.do";
    var parameter = "lsiSeq="+lsiSeq
        +"&lsId="+lsId
        +"&joNo="+joNo
        +"&joBrNo="+joBrNo;

    $.ajax({
    	url: urlName
       ,data: parameter
       ,timeout: 3000000
       ,success: function(responseText) {
            $("#ctlInfLayer").html(responseText);
            var layerHeight = 320;
            if ($("#ctlinfSize").val() == 1) {
                openCtlInfPop($("#ctlInfUrl").val());
            } else {
                $("#ctlInfLayer").css("height", layerHeight);
                $("#vwrap2").css("height", layerHeight);
                $("#viewlaCtlInf").css("height", layerHeight);
                $("#ctlInfDiv").css("height", layerHeight);
                ctlInfLayer.showCtlInfLayer();
            }
        }
    });
}

//2015.09.25 [LSI2015]  관련규제 URL 팝업호출
/**
 * <pre>
 * 	관련규제 URL 팝업호출
 * </pre>
 * @author brKim
 * @since 2017. 10. 18.
 * @param url
 * @returns {Boolean}
 */
function openCtlInfPop(url) {
	var LeftPosition = (screen.width-794) / 2;
	var TopPosition = (screen.height-462) / 2;
	var popObj = window.open(url,'lsDevCtlPop', 'scrollbars=yes,toolbar=no,resizable=yes,status=no,location=yes,menubar=no,width=800,height=700,top='+TopPosition+',left='+LeftPosition);
	
	openLinkPop(popObj);
}


var joRegul = {ordinSeq : ""
	 ,joNo : ""
	 ,joBrNo : ""
	 ,datClsCd : ""
	};

/* 규제 자치법규의 정보 제공을 위한 function */  
function joRegulatedPop(ordinSeq, joNo, joBrNo){
	
	var action = "";
	if(ordinSeq == null){
		ordinSeq = el('ordinSeq').value;
		joNo = "";
		joBrNo = "";
	}
	
	joRegul.ordinSeq = ordinSeq;
	joRegul.joNo = joNo;
	joRegul.joBrNo = joBrNo;		
	
	
	action = "ordinJoRegulatedList.do";

	joRegulateAjax(action,makeParam(joRegul));
}	

function joRegulateAjax(urlName,parameter){
	$.ajax({
		url: urlName,
		type:'POST',
		dataType:'text',
		data: parameter,
		timeout : 150000,
		success: function(responseData, result){
			var popLeft = (window.document.body.clientWidth - 690) / 2;
			$("#regLinkLayer").html(responseData).show();
			$("#regOrdin").css('left',popLeft);
			$("#regOrdin").draggable({handle : ".regOrdin_header" , containment : ".viewwrap"});
		}
	});
}

function joRegulatedPopClose(){
	$('.regOrdin').fadeOut(200);
	$('a[href^="#regOrdin-"].active').focus().removeClass('active');
}

/**
 * 법령 수동링크(하위링크)를 위한 function
 * 해당 패턴에 링크데이터가 있는지 체크하여 없으면 '하위법령 없음' 레이이를 보여준다. 
 * fncLawPop에서 분리하여 사용
 * @see fncLawPop, RegexpUtil.createLsPttnLinkInfo
 * @param LSPTTNINF_SEQ (법령패턴정보 일련번호)
 * @returns all (전체조문)- infoR 호출
 *            , jo (하위법령 팝업)
 *            , ne (안내 레이어)
 *   <pre>
 *   ┌────────────────┐
 *   │ 유형 │상위법│하위법│하위목록│
 *   ├────────────────┤
 *   │  A        O         O         O     │
 *   │  B        O         O          X     │
 *   │  C        O         X          X     │
 *   └────────────────┘
 *       jo = A
 *       ne = C
 *       all = A + B, B (B만 보여준다.)
 *   </pre>
 *   @author 오선균
 */
function fncLsPttnLinkPop(lspttninfSeq){
	$.ajax({
		method: "POST",
		url: "lsPttnLinkChk.do",
		dataType:'text',
		data : {lspttninfSeq : lspttninfSeq},
		timeout : 10000,
		success:function(data){
			if("jo" == data){
				var url = "lsLinkCommonInfo.do?lspttninfSeq=" + lspttninfSeq + "&chrClsCd=" + getValue("lsBdyChrCls");
				var size = "width=798, height=681, status=no, toolbar=no, resizable=no, scrollbars=no, menubar=no";
				
				//팝업창 중복 열림 방지
				window.open(url, '', size);
			} else if("ne" == data){
				var divId = 'joTempDeleLayer';
				lnkTitle = "<div class=\"towp2\" style=\"width:614px;\"><DIV class=ltit2 style=\"width:550px;\" id=\"tmpLtit2Link\">법령</DIV>"
					+"<div class=\"btn22\" style=\"float:right;\">"
					+"<A href=\"#AJAX\" onclick=\"javascript:TempJoDeleLayer.hiddenTempLsLinkLayer();return false;\"><IMG class=maJoHst alt=닫기 src=\"/LSW/images/button/btn_close8.gif\">"
					+"</A></DIV></div>";
				
				$("#"+divId).html("<div class=\"vwrap4\" style=\"left:0px;height:300px; width: 620px;\" id=\"contwrapLinkDiv\">"+
									"<div class=\"viewla11\" style=\"width: 614px; border-top:1px solid #ffffff;margin-top:-6px; height: 110px;\" id=\"viewLinkDiv\">"+
									"<div style=\"width:590px; height:95px; padding:10px 15px; font-family: Gulim,doutm,tahoma,sans-serif; font-size: 1.1em;\">"+
									"<div class=\"insd\" style=\"height:88px;overflow-x:hidden;overflow-y:hidden;margin-top:-1px;margin-left:0px;margin-right:0px;margin-bottom:0px\" id=\"tmpLsLinkDiv\">"+
									"<p style=\"float:left;padding:0; margin:15px 0 0 0\"><img src=\"/LSW/images/icon_alert_cirm2.gif\"></p>"+
									"<ul style=\"float:right;width:550px;\">"+
									"<li style=\"line-height:170%; padding: 0 10px 10px 10px;\"><b>조문에서 위임한 사항을 규정한 하위법령이 없습니다.</b>"+
									"<br>* 자세한 사항은 소관부처에 문의하시기 바랍니다.</li>"+
									"</ul>"+
									"</div>"+
									"</div>"+
									"</div>"+
									"</div>");
				
				TempJoDeleLayer.showTempLsLinkLayer(0,lnkTitle);
			} else if("all" == data){
				
			}
		},
		error : function(x, t, m) {
			if(t == "timeout"){
				alert("사용량이 많아 응답이 지연 있습니다 잠시 후 다시 사용하시기 바랍니다.");
			}
		}
	});
}

/**
 * 법령 수동링크에서 하위법령이 없을때 활설화되는 메세지 레이어
 */
var TempJoDeleLayer = (function() {
	
	var joTempDeleLayer = null;
	
	return {
		
		showTempLsLinkLayer : function(size, title) {
			
			if (size == 0) {
				
				if (LsLinkLayer.returnLsLinkLayer()) {
					LsLinkLayer.hiddenLsLinkLayer();
				}
				if (joTempDeleLayer) {
					joTempDeleLayer.dialog('close');
				}
				
				joTempDeleLayer = $("#joTempDeleLayer").dialog({
					autoScroll:false
					,title: title
					,width: 620
					,height: 145
					,modal : false
					,resizable : false
					,position : {
						// 내 객체 위치
						my : 'center',
						// 참조할 객체 위치
						at : 'center',
						// 참조할 객체 지정
						of : $('body')
					}
				});
				
				joTempDeleLayer.dialog("open");
			}
		}
		,hiddenTempLsLinkLayer : function(){
			if(joTempDeleLayer){
				joTempDeleLayer.dialog('close');
			}
		}
		,returnJoTempDeleLayer : function() {
			return joTempDeleLayer;
		}
	};
}());

function lsLinkCommonPrint(para) {
    var para = para;
    var url = "";
    
    if (!para) {
    	para = document.location.href.split("?").pop();
    	para = decodeURIComponent(para);
    }

	if (para.indexOf("lsJoLnkSeq") > -1 || para.indexOf("lspttninfSeq") > -1) {
		url = "lsLinkCommonInfo.do?"+para+"&print=print";
	}else if(para.indexOf("ordinlnkpttnSeq") > -1){
		url = "ordinLinkPttnPop.do?"+para+"&print=print";
	}
	openPrintPop(url,"링크정보출력");
}
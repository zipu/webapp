//시계
setInterval(() => {
    $('#header').text(gettime().toLocaleString('kr-KR'));
}, 1000);

//환율
get_currency_rates();
setInterval(get_currency_rates, 60*60*1000); //한시간마다 갱신
    
//엑세스 토큰 가져오기
var access_token;
var etflist; //etf 목록
$.get( $(location).attr('href')+"?action=get_access_token")
.done(function(res){
  if (res.success){
        log("접근 토큰 발행 성공");
        access_token = res.data;
        etflist = res.etflist;
    
        //웹소켓 연결
        connect_websocket();
        itemScreen.entries(); //보유종목 화면 시작
  } else {
        log("접근 토큰 발행 실패 :");
        log(res.data);
      }
})
.done(function(){
    //주문체결 목록
    getTransactions();
    setInterval(get_currency_rates, 60*1000); //1분마다 갱신
});



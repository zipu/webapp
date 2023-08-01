//웹소켓 테스트
var ws;
const connect_websocket = function() {
  ws = new WebSocket('wss://openapi.ebestsec.co.kr:9443/websocket');
  let today = datetime.today().date;
  ws.onopen = function() {
    // subscribe to some channels
    console.log("웹소켓 연결 완료");
  };

  ws.onmessage = function(e) {
    let data = JSON.parse(e.data);
    if (data.body != null){
     if (data.body.price != null){
      let price = parseInt(data.body.price);
      let timestamp = datetime.timestamp(today, data.body.chetime);
      real_chart.series[0].addPoint([timestamp, price]);
      };
    };
  };

  ws.onclose = function(e) {
    console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
    setTimeout(function() {
      connect_websocket();
    }, 1000);
  };
  ws.onerror = function(err) {
    console.error('Socket encountered error: ', err.message, 'Closing socket');
    ws.close();
  };

  return ws;
};


const realtime_price = function(shcode, type){
  console.log("?")
  ws.send(JSON.stringify({
    "header":{      
      "token": access_token,
      "tr_type": type //1:계좌 등록, 2:계좌해제, 3:시세등록, 4:시세해제
  },
  "body":{
      "tr_cd": "S3_",
      "tr_key":shcode
  }
  }));
}

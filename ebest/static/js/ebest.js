const url = $(location).attr('href');
var logs = [];
var realtime;

/* 인터페이스 관련 */
// 종목 tab 활성화
const activateTab = function(id){
  $('#tabs > li > a').each(function(i,a){
    if (a.id == id) { $(a).addClass('active');}
    else { $(a).removeClass('active'); }
  })
};


//시계
const gettime = function(){
    ctime = new Date();
    ktime = ctime.getTime() + (ctime.getTimezoneOffset() + 540)*60*1000;
    return new Date(ktime);
}

setInterval(() => {
    $('#header').text(gettime().toLocaleString('kr-KR'));
}, 1000);

//서버 메세지 로그
const log = function(msg){
    logs.push(msg);
    logs = logs.slice(-10);
    $('#log').html(logs.join('<br/>'));
}

//엑세스 토큰 발행

$.get( url+"?action=get_access_token", function( data ) {
  if (data.success){
       log("엑세스 토큰 발행 성공")
  } else {
       log("엑세스 토큰 발행 실패");
  }
});

//종목 현황
const itemScreen = function(tabid){
  activateTab(tabid);//탭 액티브 활성화
  clearInterval(realtime);

  if (tabid == 'entries-tab'){
    $('#item-screen > thead').append(`
      <tr>
        <td style='width:30%'> 종목 </td>
        <td style='width:20%'> 매입가 </td>
        <td style='width:10%'> 수량 </td>
        <td style='width:20%'> 현재가 </td>
        <td style='width:20%'> 대비 </td>
      </tr>
      `);
    
    let query = "?action=entries";
    $.get( url+query, function( data ) {
      if (data.success){
        log(data.msg);
        for (item of data.data){
          entryprice = parseInt(item.entryprice);
          price = parseInt(item.price);
          diff = price - entryprice
          diff > 0 ? color = 'red' : color = 'blue';

          let tr = `<tr id=${item.expcode} onclick="chartdata('${item.expcode}');">
                        <td style='width:30%'>${item.hname}</td>
                        <td style='width:20%'>${entryprice.toLocaleString('en-US')}</td>
                        <td style='width:10%'>${parseInt(item.quantity).toLocaleString('en-US')}</td>
                        <td style='width:20%'>${price.toLocaleString('en-US')}</td>
                        <td style='width:20%; color:${color}'>${diff.toLocaleString('en-Us')}</td>
                    </tr>`
          $('#item-screen > tbody').append(tr);
        };
        realtime = setInterval(() => {
          $.get( url+query, function( data ) {
            if (data.success){
              for (item of data.data){
                diff = parseInt(item.price) - parseInt(entryprice)
                diff > 0 ? color = 'red' : color = 'blue';
                $(`#${item.shcode} td:nth-child(1)`).text(parseInt(item.entryprice).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(2)`).text(parseInt(item.quantity).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(3)`).text(parseInt(item.price).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(4)`).text(diff);
                $(`#${item.shcode} td:nth-child(4)`).css('color', color);
              };
              //log("업데이트..");
            } 
          });
        }, 1000);
      };
    });
  }; //잔고 화면 끝.
};
itemScreen('entries-tab'); //최초에 잔고



// 관심종목 화면
(function favorites(){
  var query = "?action=favorites"
  $.get( url+query, function( data ) {
      if (data.success){
        log("관심종목 불러오기 성공")
        for (item of data.data){
          item.sign == '2' ? sign='+' : sign='-';
          let tr = `<tr id=${item.shcode} onclick="chartdata('${item.shcode}');">
                        <td style="width:34.8%">${item.hname}</td>
                        <td style="width:10.3%">${item.shcode}</td>
                        <td style="width:14.5%">${parseInt(item.price).toLocaleString('en-US')}</td>
                        <td style="width:14.4%">${sign+parseInt(item.change).toLocaleString('en-US')}</td>
                        <td style="width:14.3%">${parseInt(item.volume).toLocaleString('en-US')}</td>
                        <td style="width:14.3%">${item.diff}</td>
                    </tr>`
          $('#favorites').append(tr);
        };
        setInterval(() => {
          $.get( url+query, function( data ) {
            if (data.success){
              for (item of data.data){
                item.sign == '2' ? sign='+' : sign='-';
                $(`#${item.shcode} td:nth-child(3)`).text(parseInt(item.price).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(4)`).text(sign+parseInt(item.change).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(5)`).text(parseInt(item.volume).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(6)`).text(item.diff);
              };
              //log("업데이트..");
            } 
          });
        }, 500);
        
      } else {
        log("관심종목 불러오기 실패");
        favorites();
      }
  });
})();

//차트화면
// create the chart
var chart = Highcharts.stockChart('chart', {
  rangeSelector: {
      selected: 1
  },
  plotOptions: {
    candlestick: {
        color: 'blue',
        lineColor: 'blue',
        upColor: 'red',
        upLineColor: 'red',
    }
  },
  series: [{
      type: 'candlestick',
      dataGrouping: {
        enabled: false,
        units: [
            [
                'week', // unit name
                [1] // allowed multiples
            ]
        ]
    }
  }]
});


const chartdata = function(shcode){
  let query = `?action=chartdata&params=${shcode}`
  let name = $(`#${shcode} td:nth-child(1)`).text();
  $.get( url+query, function( data ) {
    if (data.success){
      log("차트데이터 불러오기 성공");
      let quotes = []
      for (quote of data.data){
        date = new Date(quote.date.slice(0,4)+'/'+quote.date.slice(4,6)+'/'+quote.date.slice(6));
        timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
        quotes.push([timestamp, quote.open, quote.high, quote.low, quote.close]);
      };
      chart.series[0].update({data: quotes, name:name});
      $("#chart-title").text(name);
      
    } else {
      log("차트데이터 불러오기 실패")
      console.log(data.data)
    }

  });
};



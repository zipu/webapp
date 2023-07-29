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
    text = `[${gettime().toLocaleString()}] ${msg}`
    logs.push(text);
    logs = logs.slice(-10);
    $('#log').html(logs.join('<br/>'));
}


//종목 현황
const itemScreen = function(tabid){
  activateTab(tabid);//탭 액티브 활성화
  clearInterval(realtime);

  if (tabid == 'entries-tab'){
    $('#item-screen > thead').html('');
    $('#item-screen > tbody').html('');
    $('#item-screen > tbody').attr('id','entries-tbody')
    $('#item-screen > thead').append(`
      <tr style='font-size:0.8em'>
        <th style='width:30%'> 종목 </th>
        <th style='width:20%'> 매입가 </th>
        <th style='width:10%'> 수량 </th>
        <th style='width:20%'> 현재가 </th>
        <th style='width:20%'> 대비 </th>
      </tr>
      `);
    
    $.get( url+"?action=entries", function( data ) {
      if (data.success){
        log(data.msg);
        for (item of data.data){
          entryprice = parseInt(item.entryprice);
          price = parseInt(item.price);
          diff = price - entryprice
          diff > 0 ? color = 'red' : color = 'blue';

          let tr = `<tr id=${item.expcode} onclick="create_chart('${item.expcode}');">
                        <td style='width:30%'>${item.hname}</td>
                        <td style='width:20%'>${entryprice.toLocaleString('en-US')}</td>
                        <td style='width:10%'>${parseInt(item.quantity).toLocaleString('en-US')}</td>
                        <td style='width:20%'>${price.toLocaleString('en-US')}</td>
                        <td style='width:20%; color:${color}'>${diff.toLocaleString('en-Us')}</td>
                    </tr>`
          
          if ($('#item-screen > tbody').attr('id')=='entries-tbody') {
            $('#item-screen > tbody').append(tr);
          };
        };
        realtime = setInterval(() => {
          $.get( url+"?action=entries", function( data ) {
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
  } //잔고 화면 끝.
  //ETF 화면
  else if (tabid == 'etf-tab'){
    $('#item-screen > thead').html('');
    $('#item-screen > tbody').html('');
    $('#item-screen > tbody').attr('id','etf-tbody');
    $('#item-screen > thead').append(`
      <tr style='font-size:0.8em';>
        <th style='width:40%'> 종목 </th>
        <th style='width:20%'> 현재가 </th>
        <th style='width:10%'> 대비 </th>
        <th style='width:10%'> 등락률 </th>
        <th style='width:20%'> 거래량 </th>
      </tr>
      `);
    
    $.get( url+"?action=etf", function( data ) {
      if (data.success){
        log("ETF 불러오기 성공")
        for (item of data.data){
          item.sign == '2' ? sign='+' : sign='-';
          item.sign == '2' ? color='red' : color='blue';
          let tr = `<tr id=${item.shcode} onclick="create_chart('${item.shcode}');">
                        <td style="width:40%">${item.hname}</td>
                        <td style="width:20%;color:${color}">${parseInt(item.price).toLocaleString('en-US')}</td>
                        <td style="width:10%;color:${color}">${sign+parseInt(item.change).toLocaleString('en-US')}</td>
                        <td style="width:10%;color:${color}">${item.diff}</td>
                        <td style="width:20%">${parseInt(item.volume).toLocaleString('en-US')}</td>
                    </tr>`
          if ($('#item-screen > tbody').attr('id')=='etf-tbody') {
                      $('#item-screen > tbody').append(tr);
          };
        };
        realtime = setInterval(() => {
          $.get( url+"?action=etf", function( data ) {
            if (data.success){
              for (item of data.data){
                item.sign == '2' ? sign='+' : sign='-';
                item.sign == '2' ? color='red' : color='blue';
                $(`#${item.shcode} td:nth-child(2)`).text(parseInt(item.price).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(2)`).css('color',color)
                $(`#${item.shcode} td:nth-child(3)`).text(sign+parseInt(item.change).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(3)`).css('color',color)
                $(`#${item.shcode} td:nth-child(5)`).text(parseInt(item.volume).toLocaleString('en-US'));
                $(`#${item.shcode} td:nth-child(4)`).text(item.diff);
                $(`#${item.shcode} td:nth-child(4)`).css('color',color)
              };
              //log("업데이트..");
            } 
          });
        }, 500);
      }
    });
  } //etf 화면 끝.
  // 업종 화면
  else if (tabid == 'sectors-tab'){
    $('#item-screen > thead').html('');
    $('#item-screen > tbody').html('');
    $('#item-screen > tbody').attr('id','sector-tbody');
    
    $.get( url+"?action=sector_list", function( data ) {
      if (data){
        log("업종 목록 불러오기 성공")
        for (item of data){
          let tr = `<tr style='font-size:0.9em;'>
                        <th style="width:33.3%" id='${item[0].upcode}' onclick="create_sector_chart('${item[0].upcode}');">${item[0].hname}</th>
                        <th style="width:33.3%" id='${item[1].upcode}' onclick="create_sector_chart('${item[1].upcode}');">${item[1].hname}</th>
                        <th style="width:33.3%" id='${item[2].upcode}' onclick="create_sector_chart('${item[2].upcode}');">${item[2].hname}</th>
                    </tr>`
          if ($('#item-screen > tbody').attr('id')=='sector-tbody') {
                      $('#item-screen > tbody').append(tr);
          };
        };
      }
    });
  }; //업종 화면 끝.
};
itemScreen('entries-tab'); //최초에 잔고



// 관심종목 화면
function favorites(){
  $.get( url+"?action=favorites", function( data ) {
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
          $.get( url+"?action=favorites", function( data ) {
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
}





//차트화면
const create_chart = function(shcode){
  $('#chart-period-day').attr('onclick', `stockchart('${shcode}','2')`);
  $('#chart-period-week').attr('onclick', `stockchart('${shcode}','3')`);
  $('#chart-period-month').attr('onclick', `stockchart('${shcode}','4')`);
  stockchart(shcode, '2');
};


const stockchart = function(shcode, period){
  let query = `?action=stockchart&params=${shcode},${period}`
  let name = $(`#${shcode} td:nth-child(1)`).text();
  $.get( url+query, function( data ) {
    if (data.success){
      log("차트데이터 불러오기 성공");
      let quotes = []
      let volume = []
      for (quote of data.data){
        date = new Date(quote.date.slice(0,4)+'/'+quote.date.slice(4,6)+'/'+quote.date.slice(6));
        timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
        quotes.push([timestamp, quote.open, quote.high, quote.low, quote.close]);
        volume.push([timestamp, quote.value])
      };
      chart.series[0].update({data: quotes, name:name});
      chart.series[1].update({data: volume, name:'거래량'});
      //$('#chart-title').text(name);
      if (period=='2'){
          COT(shcode); //투자자별 매매 동향
      } else {
        chart.series.slice(2).forEach(series =>{
          series.update({data: '', name:''});
        });
      };
      
    } else {
      log(`차트데이터 불러오기 실패:${data.msg}`);
      
    }

  });
};

//업종차트
const create_sector_chart = function(shcode){
  $('#chart-period-day').attr('onclick', `sector_chart('${shcode}','2')`);
  $('#chart-period-week').attr('onclick', `sector_chart('${shcode}','3')`);
  $('#chart-period-month').attr('onclick', `sector_chart('${shcode}','4')`);
  sector_chart(shcode, '2');
};

const sector_chart = function(shcode,period){
  //chart 주기 버튼 세팅
  
  let query = `?action=sector_chart&params=${shcode},${period}`
  let name = $(`#${shcode}`).text();

  $.get( url+query, function( data ) {
    if (data.success){
      log("차트데이터 불러오기 성공");
      let quotes = [];
      let volume = [];
      for (quote of data.data){
        date = new Date(quote.date.slice(0,4)+'/'+quote.date.slice(4,6)+'/'+quote.date.slice(6));
        timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
        quotes.push([timestamp, parseFloat(quote.open), parseFloat(quote.high), parseFloat(quote.low), parseFloat(quote.close)]);
        volume.push([timestamp, quote.jdiff_vol])
      };
      chart.series.slice(2).forEach( series => {
          series.update({data:[]});
      });

      chart.series[0].update({data: quotes, name:name}); //candle
      chart.series[1].update({data: volume, name:'거래량'}); //volume
      chart.setTitle({'text':name});

      if (period=='2'){
        market_COT(shcode); //업종 cot
      } else {
        chart.series.slice(2).forEach(series =>{
            series.update({data: '', name:''});
        });
      };
    } else {
      log("차트데이터 불러오기 실패")
      console.log(data.data)
    }

  });
};

// 투자자별 매매 동향
const COT = function(shcode){
  let query = `?action=COT&params=${shcode}`
  $.get( url+query, function( res ) {
    if (res.success){
      log("투자자별 매매동향 불러오기(COT)");
      let indivisuals =  [];
      let institutions = [];
      let foreigners = [];
      let short_sellers = [];
      let programs = [];
      
      //50 거래일 전날에 모든 값을 0으로 세팅
      idx = res.data.length - 50;
      initials = res.data[idx]; 

      for (item of res.data){
        date = new Date(item[0].slice(0,4)+'/'+item[0].slice(4,6)+'/'+item[0].slice(6));
        timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
        
        indivisuals.push([timestamp, item[1]-initials[1]]);
        institutions.push([timestamp, item[2]-initials[2]]);
        foreigners.push([timestamp, item[3]-initials[3]]);
        short_sellers.push([timestamp, item[5]-initials[5]]);
        programs.push([timestamp, item[4]-initials[4]]);
      };
      chart.series[2].update({data: indivisuals, name:'개인'});
      chart.series[3].update({data: institutions, name:'기관'});
      chart.series[4].update({data: foreigners, name:'외인'});
      chart.series[5].update({data: programs , name:'프로그램'});
      chart.series[6].update({data: short_sellers, name:'공매도'});

    } else {
      log("투자자별 매매 동향 불러오기 실패")
    };
  });
};

//업종 cot
const market_COT = function(shcode){
  let query = `?action=market_COT&params=${shcode}`
  $.get( url+query, function( res ) {
    if (res.success){
      log("투자자별 매매동향 불러오기(COT)");
      let indivisuals =  [];
      let institutions = [];
      let foreigners = [];
      let countries = [];
      
      //50 거래일 전날에 모든 값을 0으로 세팅
      idx = res.data.length - 50;
      initials = res.data[idx]; 

      for (item of res.data){
        date = new Date(item[0].slice(0,4)+'/'+item[0].slice(4,6)+'/'+item[0].slice(6));
        timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
        
        indivisuals.push([timestamp, item[1]-initials[1]]);
        institutions.push([timestamp, item[2]-initials[2]]);
        foreigners.push([timestamp, item[3]-initials[3]]);
        countries.push([timestamp, item[4]-initials[4]]);
      };
      chart.series[2].update({data: indivisuals, name:'개인'});
      chart.series[3].update({data: institutions, name:'기관'});
      chart.series[4].update({data: foreigners, name:'외인'});
      chart.series[5].update({data: countries, name:'국가'});
      chart.series[6].update({data:'', name:''})
    } else {
      log("투자자별 매매 동향 불러오기 실패")
    };
  });
}



const get_currency_rates = function(){
  $.get( url+'?action=get_currency_rate', function( data ) {
    ['USD','EUR','JPY','CNY'].forEach( (name, i) => {
      rates = []
      initial  = parseFloat(data[name][0][2])//초기값
      data[name].forEach(rate => {
        date = new Date(rate[0]+'T'+rate[1]);
        timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
        rates.push([timestamp, parseFloat(rate[2])/initial]);
      });
      currency_chart.series[i].update({data: rates, name:name});
    })
  });
  log("환율 갱신")
};
get_currency_rates();
setInterval(get_currency_rates, 60*60*1000); //한시간마다 갱신
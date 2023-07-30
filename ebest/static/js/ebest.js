const url = "https://openapi.ebestsec.co.kr:8080"; //$(location).attr('href');

var logs = [];
var realtime;
var access_token;
var etftlist; //etf 목록

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

//메세지 로그
const log = function(msg){
    let text = `[${gettime().toLocaleString()}] ${msg}`
    logs.push(text);
    logs = logs.slice(-10);
    $('#log').html(logs.join('<br/>'));
}

//접근 토큰 발급 및 django 서버에서 초기값 불러오기
$.get( $(location).attr('href')+"?action=get_access_token")
.done(function(res){
  if (res.success){
    log("접근 토큰 발행 성공");
    access_token = res.data;
    etflist = res.etflist;
    entries(); //보유종목 화면 시작
  } else {
    log("접근 토큰 발행 실패 :");
    log(res.data);
  }
})

//보유 종목 조회
const entries = function(){
  activateTab('entries-tab');
  // 1. 화면 정리
  clearInterval(realtime);
  $('#item-screen > thead').html('');
  $('#item-screen > tbody').html('');
  $('#item-screen > tbody').attr('id','entries-tbody')
  $('#item-screen > thead').append(`
    <tr style='font-size:0.8em'>
      <th style='width:5%'> </th>  
      <th style='width:30%'> 종목 </th>
      <th style='width:20%'> 매입가 </th>
      <th style='width:10%'> 수량 </th>
      <th style='width:20%'> 현재가 </th>
      <th style='width:15%'> 평가손익 </th>
    </tr>
    `);
  // 2. 보유종목 불러오기
  let path = url+"/stock/accno";
  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"t0424", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };
  let data = JSON.stringify({
      "t0424InBlock": {
      "prcgb": "",
      "chegb": "",
      "dangb": "",
      "charge": "",
      "cts_expcode": ""
    }
  });

  $.ajax({
    url: path,
    type: 'post',
    headers: headers,
    data: data
  })
  .done(function(res){
    console.log(res)
    log("보유 종목 조회: "+res.rsp_msg);
    
    let data = res['t0424OutBlock1'];
    for (let item of data){
      let entryprice = parseInt(item.pamt);
      let price = parseInt(item.price);
      let profit = parseInt(item.dtsunik);
      let color;
      profit > 0 ? color = 'red' : color = 'blue';

      let tr = `<tr id=${item.expcode} onclick="create_chart('${item.expcode}');">
                    <td style='width:5%;cursor:pointer' onclick="test();">&#128203</td>
                    <td style='width:30%'>${item.hname}</td>
                    <td style='width:20%'>${entryprice.toLocaleString('en-US')}</td>
                    <td style='width:10%'>${parseInt(item.janqty).toLocaleString('en-US')}</td>
                    <td style='width:20%'>${price.toLocaleString('en-US')}</td>
                    <td style='width:15%; color:${color}'>${profit.toLocaleString('en-Us')}</td>
                </tr>`
      
      if ($('#item-screen > tbody').attr('id')=='entries-tbody') {
        $('#item-screen > tbody').append(tr);
      };
    };
   })
  .done(function(){
    realtime = setInterval(() => {
      $.ajax({
        url: path,
        type: 'post',
        headers: headers,
        data: data
      })
      .done(function(res){
        let data = res['t0424OutBlock1'];
        for (let item of data){
          if ($('#item-screen > tbody').attr('id')=='entries-tbody') {
            let price = parseInt(item.price);
            let profit = parseInt(item.dtsunik);
            let color;
            profit > 0 ? color = 'red' : color = 'blue';
            $(`#${item.shcode} td:nth-child(4)`).text(price.toLocaleString('en-US'));
            $(`#${item.shcode} td:nth-child(5)`).text(profit);
            $(`#${item.shcode} td:nth-child(5)`).css('color', color);
          };
        };
      })
    }, 1000);
  });
};
// 잔고화면 끝

// etf 화면
const etf = function(){
  activateTab('etf-tab');
  // 1. 화면 정리
  clearInterval(realtime);
  $('#item-screen > thead').html('');
  $('#item-screen > tbody').html('');
  $('#item-screen > tbody').attr('id','etf-tbody')
  $('#item-screen > thead').append(`
    <tr style='font-size:0.8em'>
      <th style='width:30%'> 종목 </th>
      <th style='width:20%'> 매입가 </th>
      <th style='width:10%'> 수량 </th>
      <th style='width:20%'> 현재가 </th>
      <th style='width:20%'> 평가손익 </th>
    </tr>
    `);
  // 2. 보유종목 불러오기
  let path = "/stock/market-data";
  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"t8407", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };
  let data = JSON.stringify({
    "t8407InBlock" : {
        "nrec" : etflist.length,
        "shcode": etflist.join('')
    }
  });

  $.ajax({
    url: url+path,
    type: 'post',
    headers: headers,
    data: data
  })
  .done(function(res){
    console.log(res)
    log("ETF 조회: "+res.rsp_msg);
    
    let data = res['t8407OutBlock1'];
    for (let item of data){
      let sign;
      let color;
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
   })
  .done(function(){ //1초마다 반복 조회 
    realtime = setInterval(() => {
      $.ajax({
        url: url+path,
        type: 'post',
        headers: headers,
        data: data
      })
      .done(function(res){
        let data = res['t8407OutBlock1'];
        for (let item of data){
          if ($('#item-screen > tbody').attr('id')=='entries-tbody') {
            let sign;
            let color;
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
        };
      });
    }, 1000);
  });
};
// etf 화면 끝

// 업종 화면
const sectors = function(){
  activateTab('sectors-tab');
  // 1. 화면 정리
  clearInterval(realtime);
  $('#item-screen > thead').html('');
  $('#item-screen > tbody').html('');
  $('#item-screen > tbody').attr('id','sectors-tbody')
  
  // 2. 업종 목록 불러오기
  let path = "/indtp/market-data"
  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"t8424", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };
  let data = JSON.stringify({
    "t8424InBlock" : {
        "gubun1":"0"
    }
  });

  $.ajax({
    url: url+path,
    type: 'post',
    headers: headers,
    data: data
  })
  .done(function(res){
    console.log(res)
    log("업종 목록 조회: "+res.rsp_msg);
    let data = res['t8424OutBlock'];
    let kospi = [];
    let kp200 = [];
    let kosdaq = [];
    data.forEach(item => {
      if (item.upcode[0] == '0') { kospi.push(item)}
      else if (item.upcode[0] == '1') { kp200.push(item)}
      else if (item.upcode[0] == '3') { kosdaq.push(item)}
    });
    let idx = Math.max(kospi.length, kp200.length, kosdaq.length);
    let items = [];
    for (let i = 0; i<idx; i++){
      if (!kospi[i]) { kospi[i] = {"hname":"", "upcode":""}};
      if (!kp200[i]) { kp200[i] = {"hname":"", "upcode":""}};
      if (!kosdaq[i]) { kosdaq[i] = {"hname":"", "upcode":""}};
      items.push([kospi[i], kp200[i], kosdaq[i]]);
    };
    for (item of items){
      let tr = `<tr style='font-size:0.9em;'>
                    <th style="width:33.3%" id='${item[0].upcode}' onclick="create_sector_chart('${item[0].upcode}');">${item[0].hname}</th>
                    <th style="width:33.3%" id='${item[1].upcode}' onclick="create_sector_chart('${item[1].upcode}');">${item[1].hname}</th>
                    <th style="width:33.3%" id='${item[2].upcode}' onclick="create_sector_chart('${item[2].upcode}');">${item[2].hname}</th>
                </tr>`
      if ($('#item-screen > tbody').attr('id')=='sectors-tbody') {
                  $('#item-screen > tbody').append(tr);
      };
    };
   });
};


//차트화면
const create_chart = function(shcode){
  $('#chart-period-day').attr('onclick', `stockchart('${shcode}','2')`);
  $('#chart-period-week').attr('onclick', `stockchart('${shcode}','3')`);
  $('#chart-period-month').attr('onclick', `stockchart('${shcode}','4')`);
  stockchart(shcode, '2');
};


const stockchart = function(shcode, period){
  let path = "/stock/chart"
  let name = $(`#${shcode} td:nth-child(1)`).text();
  
  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"t8410", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };
  let data = JSON.stringify({
    "t8410InBlock" : {
        "shcode" : shcode,
        "gubun" : period,
        "qrycnt" : 500,
        "sdate" : "",
        "edate" : gettime().toJSON().slice(0,10).replaceAll('-',''),
        "cts_date" : "",
        "comp_yn" : "N",
        "sujung" : "Y"
    }
  });

  $.ajax({
    url: url+path,
    type: 'post',
    headers: headers,
    data: data
  })
  .done(function(res){
    log("차트데이터 불러오기 성공");
    data = res['t8410OutBlock1'];  
    
    let quotes = []
    let volume = []
    for (quote of data){
      date = new Date(quote.date.slice(0,4)+'/'+quote.date.slice(4,6)+'/'+quote.date.slice(6));
      timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
      quotes.push([timestamp, quote.open, quote.high, quote.low, quote.close]);
      volume.push([timestamp, quote.value])
    };
    chart.series[0].update({data: quotes, name:name});
    chart.series[1].update({data: volume, name:'거래량'});
    $('#chart-title').text(name);
    if (period=='2'){
        COT(shcode); //투자자별 매매 동향
    } else {
      chart.series.slice(2).forEach(series =>{
        series.update({data: '', name:''});
      });
    };
  })
  .fail(function(res){
    log("차트데이터 불러오기 실패: "+res);
  })
};

// 투자자별 매매 동향
const COT = function(shcode){
  let path = "/stock/frgr-itt"
  let today = gettime();
  let start = new Date(gettime()-500*24*60*60*1000);

  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"t1716", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };
  let data = JSON.stringify({
      "t1716InBlock" : {
          "shcode" : shcode,
          "gubun" : "1",
          "fromdt" : start.toJSON().slice(0,10).replaceAll('-',''),
          "todt" : today.toJSON().slice(0,10).replaceAll('-',''),
          "prapp" : 0,
          "prgubun" : "0",
          "orggubun" : "0",
          "frggubun" : "0"
      }
  });
  $.ajax({
    url: url+path,
    type: 'post',
    headers: headers,
    data: data
  })
  .done(function(res){
    log("투자자별 매매동향 불러오기: "+res.rsp_msg);
    let indivisuals =  [];
    let institutions = [];
    let foreigners = [];
    let short_sellers = [];
    let programs = [];

    //50 거래일 전날에 모든 값을 0으로 세팅
    let data = res['t1716OutBlock'].reverse();
    let idx = data.length - 50;
    let initials;
    idx > 0? initials = data[idx] : initials = data[0]; 
    for (item of data){
      let datestring = item.date;
      let date = new Date(datestring.slice(0,4)+'/'+datestring.slice(4,6)+'/'+datestring.slice(6));
      let timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
      
      indivisuals.push([timestamp, item['krx_0008']-initials['krx_0008']]);
      institutions.push([timestamp, item['krx_0018']-initials['krx_0018']]);
      foreigners.push([timestamp, item['fsc_0009']-initials['fsc_0009']]);
      short_sellers.push([timestamp, item['gm_volume']-initials['gm_volume']]);
      programs.push([timestamp, item['pgmvol']-initials['pgmvol']]);
    };
    chart.series[2].update({data: indivisuals, name:'개인'});
    chart.series[3].update({data: institutions, name:'기관'});
    chart.series[4].update({data: foreigners, name:'외인'});
    chart.series[5].update({data: programs , name:'프로그램'});
    chart.series[6].update({data: short_sellers, name:'공매도'});
  });
      
};



//업종차트
const create_sector_chart = function(shcode){
  $('#chart-period-day').attr('onclick', `sector_chart('${shcode}','2')`);
  $('#chart-period-week').attr('onclick', `sector_chart('${shcode}','3')`);
  $('#chart-period-month').attr('onclick', `sector_chart('${shcode}','4')`);
  sector_chart(shcode, '2');
};

const sector_chart = function(shcode, period){

  //업종 차트
  let path = "/indtp/chart";
  let name = $(`#${shcode} td:nth-child(1)`).text();
  
  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"t8419", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };
  let data = JSON.stringify({
      "t8419InBlock": {
          "shcode": shcode,
          "gubun": period,
          "qrycnt": 500,
          "sdate": " ",
          "edate": "99999999",
          "cts_date": " ",
          "comp_yn": "N"
      }
  });
  $.ajax({
    url: url+path,
    type: 'post',
    headers: headers,
    data: data
  })
  .done(function(res){
    log("차트데이터 불러오기 성공");
    data = res['t8419OutBlock1'];  
    let quotes = []
    let volume = []
    for (quote of data){
      date = new Date(quote.date.slice(0,4)+'/'+quote.date.slice(4,6)+'/'+quote.date.slice(6));
      timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
      quotes.push([timestamp, parseFloat(quote.open), parseFloat(quote.high), parseFloat(quote.low), parseFloat(quote.close)]);
      volume.push([timestamp, parseInt(quote.value)])
    };
    chart.series[0].update({data: quotes, name:name});
    chart.series[1].update({data: volume, name:'거래량'});
    //$('#chart-title').text(name);
    if (period=='2'){
        sector_COT(shcode); //투자자별 매매 동향
    } else {
      chart.series.slice(2).forEach(series =>{
        series.update({data: '', name:''});
      });
    };
  })
  .fail(function(res){
    log("차트데이터 불러오기 실패: "+res.rsp_msg);
  });
};



//업종 cot
const sector_COT = function(shcode){
  let path = "/stock/chart"
  let today = gettime();
  let start = new Date(gettime()-500*24*60*60*1000);

  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"t1665", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };
  let data = JSON.stringify({
      "t1665InBlock" : {
          "market" : shcode[0],
          "upcode": shcode,
          "gubun2": "2",
          "gubun3": "1", 
          "from_date" : start.toJSON().slice(0,10).replaceAll('-',''),
          "to_date" : today.toJSON().slice(0,10).replaceAll('-',''),
      }
  });
  $.ajax({
    url: url+path,
    type: 'post',
    headers: headers,
    data: data
  })
  .done(function(res){
    log("투자자별 매매동향 불러오기: "+res.rsp_msg);
    let indivisuals =  [];
    let institutions = [];
    let foreigners = [];
    let countries = [];

    //50 거래일 전날에 모든 값을 0으로 세팅
    let data = res['t1665OutBlock1'].reverse();
    let idx = data.length - 50;
    let initials;
    idx > 0? initials = data[idx] : initials = data[0]; 
    for (item of data){
      let datestring = item.date;
      let date = new Date(datestring.slice(0,4)+'/'+datestring.slice(4,6)+'/'+datestring.slice(6));
      let timestamp = date.getTime()+date.getTimezoneOffset()*60*1000;
      
      indivisuals.push([timestamp, item['sv_08']-initials['sv_08']]);
      institutions.push([timestamp, item['sv_18']-initials['sv_18']]);
      foreigners.push([timestamp, item['sv_17']-initials['sv_17']]);
      countries.push([timestamp, item['sv_11']-initials['sv_11']]);
    };
    chart.series[2].update({data: indivisuals, name:'개인'});
    chart.series[3].update({data: institutions, name:'기관'});
    chart.series[4].update({data: foreigners, name:'외인'});
    chart.series[5].update({data: countries , name:'국가'});
    chart.series[6].update({data: '', name:''});
  });
};



const get_currency_rates = function(){
  $.get( $(location).attr('href')+'?action=get_currency_rate', function( data ) {
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

const test = function(){
  //
}
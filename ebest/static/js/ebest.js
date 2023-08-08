const url = "https://openapi.ebestsec.co.kr:8080";
var test;

/* 종목 리스크 스크린 */
var selected; //현재 선택된 종목
var selected_period;
var selected_type;
var screentimer; //스크린 화면 갱신용


const itemScreen = {
  // 탭 활성화
  "activateTab": function(id){
    $('#tabs > li > a').each(function(i,a){
      if (a.id == id) { $(a).addClass('active');}
      else { $(a).removeClass('active'); }
    })
  },
  // 보유종목 탭
  "entries":  function(){
    itemScreen.activateTab('entries-tab');
    // 1. 화면 정리
    clearInterval(screentimer);
    //$('#item-screen').html('');
    $('#companies-table_wrapper').hide();
    itemScreenTables.entriesTable.find('tbody').html('');
    $('#item-screen').append(itemScreenTables.entriesTable);

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
  
        let tr = `<tr id=${item.expcode} onclick="chartScreen.init('${item.expcode}');" style="cursor:default">
                      <td style='width:5%;cursor:pointer' onclick="companyDetail('${item.expcode}')" data-bs-toggle="modal" data-bs-target="#companyModal">&#128203</td>
                      <td style='width:30%'>${item.hname}</td>
                      <td style='width:20%'>${entryprice.toLocaleString('en-US')}</td>
                      <td style='width:10%'>${parseInt(item.janqty).toLocaleString('en-US')}</td>
                      <td style='width:20%'>${price.toLocaleString('en-US')}</td>
                      <td style='width:15%; color:${color}'>${profit.toLocaleString('en-Us')}</td>
                  </tr>`
        
        if ($('#item-screen > table').attr('id')=='entries-table') {
          $('#entries-table > tbody').append(tr);
        };
      };
     })
    .done(function(){
      screentimer = setInterval(() => {
        $.ajax({
          url: path,
          type: 'post',
          headers: headers,
          data: data
        })
        .done(function(res){
          let data = res['t0424OutBlock1'];
          for (let item of data){
            if ($('#entries-table > table').attr('id')=='entries-table') {
              let price = parseInt(item.price);
              let profit = parseInt(item.dtsunik);
              let color;
              profit > 0 ? color = 'red' : color = 'blue';
              $(`#${item.shcode} td:nth-child(5)`).text(price.toLocaleString('en-US'));
              $(`#${item.shcode} td:nth-child(6)`).text(profit);
              $(`#${item.shcode} td:nth-child(6)`).css('color', color);
            };
          };
        })
      }, 1000);
    });
  },
  "companies": function(){
    itemScreen.activateTab('companies-tab');
    // 1. 화면정리
    clearInterval(screentimer);
    $('#entries-table').remove();
    $('#companies-table_wrapper').show();
  },

  "etf": function(){
    itemScreen.activateTab('etf-tab');
    // 1. 화면 정리
    clearInterval(screentimer);
    $('#item-screen > thead').html('');
    $('#item-screen > tbody').html('');
    $('#item-screen > tbody').attr('id','etf-tbody')
    $('#item-screen > thead').append(`
      <tr style='font-size:0.8em'>
        <th style='width:30%'> 종목 </th>
        <th style='width:20%'> 매입가 </th>
        <th style='width:10%'> 수량 </th>
        <th style='width:20%'> 현재가 </th>
        <th style='width:20%'> 거래량</th>
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
        let tr = `<tr id=${item.shcode} onclick="chartScreen.setButtons('${item.shcode}');">
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
      screentimer = setInterval(() => {
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
  },

  "sectors": function(){
    itemScreen.activateTab('sectors-tab');
    // 1. 화면 정리
    clearInterval(screentimer);
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
                      <th style="width:33.3%" id='${item[0].upcode}' onclick="chartScreen.initSectorChart('${item[0].upcode}');">${item[0].hname}</th>
                      <th style="width:33.3%" id='${item[1].upcode}' onclick="chartScreen.initSectorChart('${item[1].upcode}');">${item[1].hname}</th>
                      <th style="width:33.3%" id='${item[2].upcode}' onclick="chartScreen.initSectorChart('${item[2].upcode}');">${item[2].hname}</th>
                  </tr>`
        if ($('#item-screen > tbody').attr('id')=='sectors-tbody') {
                    $('#item-screen > tbody').append(tr);
        };
      };
     });
  }
};
  
//차트화면
var candletimer; //캔들 차트 갱신용
const chartScreen={
  "init": function(shcode){
    realtime_price(selected, '4'); //실시간 해제
    selected = shcode;
    selected_type = 'company'
    realtime_price(selected, '3'); //실시간 등록
  
    $('#chart-period-day').attr('onclick', `chartScreen.runCandleChart('${shcode}','2')`);
    $('#chart-period-week').attr('onclick', `chartScreen.runCandleChart('${shcode}','3')`);
    $('#chart-period-month').attr('onclick', `chartScreen.runCandleChart('${shcode}','4')`);
    $('#chart-period-min').attr('onclick', `chartScreen.runCandleChart('${shcode}','5')`);
    
    this.runCandleChart(shcode, '2');
    let name = $($(`#${shcode} > td`)[1]).text();
    googleTrends(name); //구글 트랜드 
  },

  "runCandleChart": function(shcode, period){
    clearInterval(candletimer);
    selected = shcode;
    selected_period = period;
    let minutes; 
    period == '5'? minutes = parseInt($('#minutes').val()) : minutes = null;  
    this.CandleChart(shcode, period, minutes);
    candletimer = setInterval(()=>{
      this.CandleChart(shcode, period, minutes);
    }, 2000);
  },

  "CandleChart": function(shcode, period, minutes){
    let path = "/stock/chart"
    let name = $(`#${shcode} td:nth-child(2)`).text();
    let outblock;
    let inblock;
    let headers;
    let data;

    //분차트
    if (period=='5'){
      outblock = 't8412OutBlock1';
      inblock = "t8412InBlock";
      headers = {
        "content-type":"application/json; charset=utf-8", 
        "authorization": `Bearer ${access_token}`,
        "tr_cd":"t8412", 
        "tr_cont":"N",
        "tr_cont_key":"",
      };
      data = {
          "t8412InBlock" : {
            "shcode" : shcode,
            "ncnt" : minutes,
            "qrycnt" : 500,
            "nday" : "0",
            "sdate" : "",
            "stime" : "",
            "edate" : "99999999",
            "etime" : "",
            "cts_date" : "",
            "cts_time" : "",
            "comp_yn" : "N"
          }
      };
    //일주월 차트
    } else { 
      outblock = 't8410OutBlock1';
      inblock = "t8410InBlock"
      headers = {
        "content-type":"application/json; charset=utf-8", 
        "authorization": `Bearer ${access_token}`,
        "tr_cd":"t8410", 
        "tr_cont":"N",
        "tr_cont_key":"",
      };
      data = {
        "t8410InBlock" : {
            "shcode" : shcode,
            "gubun" : period,
            "qrycnt" : 500,
            "sdate" : "",
            "edate" : datetime.today().date,
            "cts_date" : "",
            "comp_yn" : "N",
            "sujung" : "Y"
        }
      };
    };

    $.ajax({
      url: url+path,
      type: 'post',
      headers: headers,
      data: JSON.stringify(data)
    })
    .done(function(res){
      if (selected != shcode & selected_period !=period) return;

      log("차트데이터 불러오기 성공");

      let ohlc = res[outblock];  
      let quotes = []
      let volume = []
      let date;
      for (let quote of ohlc){
        if (period == '5'){
        date = datetime.timestamp(quote.date, quote.time) - 1000*60*minutes;
        } else {
          date = datetime.timestamp(quote.date);
        }
        quotes.push([date, quote.open, quote.high, quote.low, quote.close]);
        volume.push([date, quote.jdiff_vol]);
      };
      let last = quotes.length-1;
      let strdate = ohlc[last].date;
      let strtime = ohlc[last].time

      $('#cur-price').text(`현재가: ${quotes[last][4].toLocaleString('en-US')}`)
      chart.series[0].update({data: quotes, name:name}, false);
      chart.series[1].update({data: volume, name:'거래량'}, false);
      chart.setTitle({'text': name});
      chart.redraw();
      if (period=='2'){
          chartScreen.COT(shcode); //투자자별 매매 동향
      } else {
        chart.series.slice(2).forEach(series =>{
          series.update({data: '', name:''});
        });
      };
    })
    .fail(function(res){
      log("차트데이터 불러오기 실패: "+res);
    })
  },
  "COT": function(shcode){
    // 투자자별 매매 동향
    let path = "/stock/frgr-itt"

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
            "fromdt" : datetime.pastday(500).date,
            "todt" : datetime.today().date,
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
      let date;
      let idx = data.length - 50;
      let initials;
      idx > 0? initials = data[idx] : initials = data[0]; 
      for (item of data){
        date = datetime.timestamp(item.date);
        indivisuals.push([date, item['krx_0008']-initials['krx_0008']]);
        institutions.push([date, item['krx_0018']-initials['krx_0018']]);
        foreigners.push([date, item['fsc_0009']-initials['fsc_0009']]);
        short_sellers.push([date, item['gm_volume']-initials['gm_volume']]);
        programs.push([date, item['pgmvol']-initials['pgmvol']]);
      };
      chart.series[2].update({data: indivisuals, name:'개인'});
      chart.series[3].update({data: institutions, name:'기관'});
      chart.series[4].update({data: foreigners, name:'외인'});
      chart.series[5].update({data: programs , name:'프로그램'});
      chart.series[6].update({data: short_sellers, name:'공매도'});
    });
  },

  "initSectorChart": function(shcode){
    $('#chart-period-day').attr('onclick', `chartScreen.runSectorChart('${shcode}','2')`);
    $('#chart-period-week').attr('onclick', `chartScreen.runSectorChart('${shcode}','3')`);
    $('#chart-period-month').attr('onclick', `chartScreen.runSectorChart('${shcode}','4')`);
    chartScreen.runSectorChart(shcode, '2');
  },

  "runSectorChart": function(shcode, period){
    clearInterval(candletimer);
    selected = shcode;
    selected_period = period;
    selected_type = 'sector';
    chartScreen.sectorChart(shcode, period);
    candletimer = setInterval(()=>{
      chartScreen.sectorChart(shcode, period);
    }, 2010);

  },

  "sectorChart": function(shcode, period){
    //업종 차트
    let path = "/indtp/chart";
    let name = $(`#${shcode}`).text();
    
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
      let date;
      for (let quote of data){
        date = datetime.timestamp(quote.date);
        quotes.push([date, parseFloat(quote.open), parseFloat(quote.high), parseFloat(quote.low), parseFloat(quote.close)]);
        volume.push([date, parseInt(quote.value)])
      };
      chart.series[0].update({data: quotes, name:name});
      chart.series[1].update({data: volume, name:'거래량'});
      chart.setTitle({'text': name});
      if (period=='2'){
          sector_COT(shcode); //투자자별 매매 동향
      } else {
        chart.series.slice(2).forEach(series =>{
          series.update({data: '', name:''});
        });
      };
    })
    .done(function(){
      
    })
    .fail(function(res){
      log("차트데이터 불러오기 실패: "+res.rsp_msg);
    });
  }
};




//업종 cot
const sector_COT = function(shcode){
  let path = "/stock/chart"

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
          "from_date" : datetime.pastday(500).date,
          "to_date" : datetime.today().date
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
    let date;
    let idx = data.length - 50;
    let initials;
    idx > 0? initials = data[idx] : initials = data[0]; 
    for (let item of data){
      date = datetime.timestamp(item.date);
      indivisuals.push([date, item['sv_08']-initials['sv_08']]);
      institutions.push([date, item['sv_18']-initials['sv_18']]);
      foreigners.push([date, item['sv_17']-initials['sv_17']]);
      countries.push([date, item['sv_11']-initials['sv_11']]);
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
      let arr = [];
      data[name].forEach(i=>{
        arr.push(parseFloat(i[2]));
      });
      const stat = norm(arr);
      let date;
      let rates = [];
      //let initial  = parseFloat(data[name][0][2])//초기값
       
      data[name].forEach(rate => {
        date = datetime.timestamp(rate[0], rate[1]);
        rates.push([date, parseFloat((rate[2])-stat.mean)/stat.std]);
      });
      currency_chart.series[i].update({data: rates, name:name});
    })
  });
  log("환율 갱신")
};

//var transactions = [];
const getTransactions = function(){
  let path = "/stock/accno"
  let headers = {
    "content-type":"application/json; charset=utf-8", 
    "authorization": `Bearer ${access_token}`,
    "tr_cd":"CSPAQ13700", 
    "tr_cont":"N",
    "tr_cont_key":"",
  };

  let data = {
    "CSPAQ13700InBlock1" : {
      "OrdMktCode" : "00",
      "BnsTpCode" : "0",
      "IsuNo" : "",
      "ExecYn" : "1",
      "OrdDt" : "",
      "SrtOrdNo2" : 999999999,
      "BkseqTpCode" : "0", 
      "OrdPtnCode" : "00"
    }
  }

  $.ajax({
    url: url+path,
    type: 'post',
    headers: headers,
    data: JSON.stringify(data)
  })
  .done(function(res){
    log("주문체결내역 조회 성공: "+res.rsp_msg);
    console.log(res)
    let data = res["CSPAQ13700OutBlock3"];
    $('#transactions').html('');
    for (let item of data){
      let date = item['OrdDt'].slice(0,4)+'-'+item['OrdDt'].slice(4,6)+'-'+item['OrdDt'].slice(6)
      let time = item['ExecTrxTime'].slice(0,2)+':'+item['ExecTrxTime'].slice(2,4)+':'+item['ExecTrxTime'].slice(4,6)
      let row = `<tr>
        <td style="padding:0;width:22%">${date} ${time}</td>
        <td style="padding:0;width:18%">${item['IsuNm']}</td>
        <td style="padding:0;width:5%">${item['BnsTpNm']}</td>
        <td style="padding:0;width:8%">${parseInt(item['OrdPrc']).toLocaleString('en-US')}</td>
        <td style="padding:0;width:5%">${item['OrdQty']}</td>
        <td style="padding:0;width:8%">${parseInt(item['ExecPrc']).toLocaleString('en-US')}</td>
        <td style="padding:0;width:5%">${item['ExecQty']}</td>
        <td style="padding:0;width:14%">${item['OrdPtnNm']}</td>
        <td style="padding:0;width:15%">${item['CommdaNm']}</td>
      </tr>`
      $('#transactions').append(row);
    };

  });
}

const googleTrends = function(name){
  $.get( $(location).attr('href')+`?action=google_trends&params=${name}`, function( data ) {
    google_trend_chart.series[0].update({
      'data': data,
      'name': name
    })
    log("구글 트랜드 불러오기 성공");
  });
  
}

//modal 화면
var company_info;
const companyDetail = function(shcode){
  $.get( $(location).attr('href')+`?action=company_info&params=${shcode}`, function( data ) {
    log("회사 정보 불러오기 성공: " + shcode);
    company_info = data;
    $('#modal-title').text(data.info.name);

  });

};

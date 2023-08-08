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
var companies;
var itemScreenTables = {
  'entriesTable': $(`<table  class="table table-sm table-striped" id='entries-table'
                        style="display: block; width:100%;margin: 0;border:1px solid black;height:550px;overflow:auto;">
                        <thead style='display:table;width:100%;position:sticky;background-color:white;top:0'>
                        <tr style='font-size:0.8em'>
                        <th style='width:5%'> </th>  
                        <th style='width:30%'> 종목 </th>
                        <th style='width:20%'> 매입가 </th>
                        <th style='width:10%'> 수량 </th>
                        <th style='width:20%'> 현재가 </th>
                        <th style='width:15%'> 평가손익 </th>
                        </tr>
                        </thead>
                        <tbody style="display:table; width:100%;"></tbody>
                        </table>`),

    'companiesTable': $(`<table  class="table table-sm table-striped" id='companies-table'
                  style="display: block; width:100%;margin: 0;border:1px solid black;height:550px;overflow:auto;">
              <thead style='display:table;width:100%;position:sticky;background-color:white;top:0'>
              <tr style='font-size:0.8em'>
                <th style='width:5%'>  </th>
                <th style='width:23%'> 종목 </th>
                <th style='width:20%'> 거래소 </th>
                <th style='width:33%'> 시가총액 </th>
                <th style='width:18%'> 배당률 </th>
              </tr>
              </thead>
              <tbody style="display:table; width:100%;"></tbody>
            </table>`)
};

$( document ).ready(function() {
  $.get( $(location).attr('href')+`?action=company_list`, function( data ) {
    for (let item of data){
      let tr = `<tr id=${item[0]} onclick="chartScreen.init('${item[0]}');" style="cursor:default">
                    <td style='width:5%;cursor:pointer' data-bs-toggle="modal" data-bs-target="#exampleModal">&#128203</td>
                    <td style='width:23%'>${item[1]}</td>
                    <td style='width:20%'>${item[2]}</td>
                    <td style='width:33%'>${item[3]}</td>
                    <td style='width:18%'>${item[4]}</td>
                </tr>`
      
      itemScreenTables.companiesTable.append(tr);
    };

    $('#item-screen').append(itemScreenTables.companiesTable);
    $('#companies-table').DataTable();
    $('#companies-table_wrapper').hide();
  })
  .done(function(){
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
  });
});


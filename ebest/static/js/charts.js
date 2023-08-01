// 차트 세팅
Highcharts.setOptions({
    lang:{
      months : ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'],
      shortMonths:['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'],
      weekdays: ['일','월','화','수','목','금','토']
    }
});

// 1. 캔들 차트 
var chart = Highcharts.stockChart('chart', {
    credits: {
      enabled: false
    },
    title:{ 
      text: "",
      align: "left",
      floating: true,
      x: 10
    },
    xAxis:{
      dateTimeLabelFormats: {
        millisecond: '%H:%M:%S.%L',
        second: '%H:%M:%S',
        minute: '%H:%M',
        hour: '%H:%M',
        day: '%e. %b',
        week: '%b%e일',
        month: '%y\`%b',
        year: '%Y'
      }
    },
    yAxis: [{
        labels: {
            align: 'left'
        },
        height: '70%',
        resize: {
            enabled: true
        }
    }, {
        labels: {
            align: 'left'
        },
        top: '70%',
        height: '15%',
        offset: 0
    },{
      top: '85%',
      height: '15%',
      offset: 0,
    } ],
    rangeSelector: {
        selected: 2,
        inputEnabled:false,
        buttonPosition: {
          align: 'center'
        },
        buttons: [
          {
            type: 'day',
            count: 1,
            text: '1일',
        },{
            type: 'week',
            count: 1,
            text: '1주',
        }, {
            type: 'month',
            count: 3,
            text: '3개월',
        }, {
            type: 'year',
            count: 1,
            text: '1년',
            title: 'View 1 year'
        }, {
            type: 'all',
            text: 'All',
            title: 'View all'
        }]
    },
    tooltip: {
      enabled: true,
      shadow: false,
      borderWidth: 0,
      
      positioner: function() {
        return {
            x: this.chart.plotLeft,
            y: this.chart.plotTop
        };
      },
    },
    legend: {
      enabled: true
    },
    plotOptions: {
      series: {
        states: {
          inactive: {
              opacity: 1
          },
          hover: {
              enabled: false
          }
        },
        dataGrouping: {
          enabled: false,
          units: [
              [
                  'week', // unit name
                  [1] // allowed multiples
              ]
          ]
        }
      },
      candlestick: {
          color: 'blue',
          lineColor: 'blue',
          upColor: 'red',
          upLineColor: 'red',
      },
      line:{
        lineWidth: 2
      }
    },
    navigator: { enabled: false },
    series: [{
                type: 'candlestick',
                showInLegend: false, 
              },{
                  type: 'column',
                  yAxis: 1,
                  color: 'grey',
                  showInLegend: false, 
                  
              },{
                  name: '개인',
                  type: 'line',
                  yAxis: 2,
                  enableMouseTracking: false,
                  states: {inactive: { opacity: 0.1 } }
              },{
                  name: '기관',
                  type: 'line',
                  yAxis: 2,
                  enableMouseTracking: false,
                  states: {inactive: { opacity: 0.1 } }
              },{
                  name: '외인',
                  type: 'line',
                  yAxis: 2,
                  enableMouseTracking: false,
                  states: {inactive: { opacity: 0.1 } }
              },{
                  name: '프로그램',
                  type: 'line',
                  yAxis: 2,
                  enableMouseTracking: false,
                  states: {inactive: { opacity: 0.1 } }
              },{
                  name: '공매도',
                  type: 'line',
                  yAxis: 2,
                  enableMouseTracking: false,
                  states: {inactive: { opacity: 0.1 } }
              }]
  });
  // 2. 실시간 차트
  var real_chart = Highcharts.chart('real-chart', {
    credits: {
      enabled: false
    },
    xAxis: {
      type: 'datetime'
    },
    title:{
      text:''
    },
    yAxis:{
      title:''
    },
    legend:{
      enabled:false
    },
    tooltip: {
      enabled: false
    },
    plotOptions: {
      series: {
          marker: {
              enabled: false,
              states: {
                  hover: {
                      enabled: false
                  }
              }
          }
      }
    },
    series: [{
          name: '실시간',
    }]
  });
  
  
  // 3. 환율차트 
  var currency_chart = Highcharts.chart('currency-chart', {
    credits: {
      enabled: false
    },
    title: {
        text: '환율',
        floating:true,
        x: -150,
        y:239,
        style:{
          fontSize: '0.9em',
        }
    },
    xAxis: {
      type: 'datetime',
      dateTimeLabelFormats: {
        millisecond: '%H:%M:%S.%L',
        second: '%H:%M:%S',
        minute: '%H:%M',
        hour: '%H:%M',
        day: '%b%e일',
        week: '%b%e일',
        month: '%y\`%b',
        year: '%Y'
      }
    },
    yAxis:{
      title:''
    },
    tooltip: {
      enabled: false
    },
    plotOptions: {
      series: {
          marker: {
              enabled: false,
              states: {
                  hover: {
                      enabled: false
                  }
              }
          }
      }
    },
    legend:{
      y: -24,
      floating:true
    },
    series: [{
          name: 'USD',
      }, {
          name: 'EUR',
      }, {
          name: 'JPY',
      }, {
          name: 'CNY',
    }]
  });
  
  
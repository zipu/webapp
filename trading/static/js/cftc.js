var legacy_futures_chart = Highcharts.chart('legacy-futures-chart', {
    credits: {
      enabled: false
    },
    chart:{
      type:'line',
      panning: true
    },
    title: {
        text: 'Legacy - Futures',
    },
    xAxis: {
      type: 'datetime',
      crosshair:true,
    },
    yAxis:[{
      title:'Long-Short',
      height: '80%',
    },{
      title:'Traders',
      top:'80%',
      height:'20%'
    }],
    tooltip :{
      shared: true
    },
    plotOptions: {
      series: {
          states: {
            hover: {
              enabled: false
            },
            inactive: {
              opacity: 1
            }
          },
          marker: {
              enabled: false,
              states: {
                  hover: {
                      enabled: false
                  }
              }
          }
      },
    },
    series: [
      {name: 'Commercial', color:'grey' },
      {name: 'Non-commercial', color: 'red'},
      {name: 'Non-reportables', color: 'orange'},
      {name: 'Traders', yAxis:1},
    ]
});

var legacy_option_chart = Highcharts.chart('legacy-option-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: 'true',
  },
  title: {
      text: 'Legacy - Option',
  },
  xAxis: {
    type: 'datetime',
    crosshair:true
  },
  yAxis:[{
    title:'',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Commercial', color:'grey' },
    {name: 'Non-commercial', color: 'red'},
    {name: 'Non-reportables', color: 'orange'},
    {name: 'Traders', yAxis:1},
  ]
});

var legacy_spread_chart = Highcharts.chart('legacy-spread-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: true
  },
  title: {
      text: 'Legacy - Spread',
  },
  xAxis: {
    type: 'datetime',
    crosshair: true
  },
  yAxis:[{
    title:'Long-Short',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Non Commercial', color:'red' },
    {name: 'Traders', yAxis:1},
  ]
});

var disaggregated_futures_chart = Highcharts.chart('disaggregated-futures-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: true
  },
  title: {
      text: 'Disaggregated - Futures',
  },
  xAxis: {
    type: 'datetime',
    crosshair:true
  },
  yAxis:[{
    title:'Long-Short',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Commercials: producer/merchant/processor', color:'black' },
    {name: 'Commercials: swap dealers', color: 'grey'},
    {name: 'Non-commercial: managed money', color: 'red'},
    {name: 'Non-commercial: others', color: 'orange'},
    {name: 'Traders',  yAxis:1},
  ]
});

var disaggregated_option_chart = Highcharts.chart('disaggregated-option-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: true
  },
  title: {
      text: 'Disaggregated - Option',
  },
  xAxis: {
    type: 'datetime',
    crosshair: true
  },
  yAxis:[{
    title:'Long-Short',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Commercials: producer/merchant/processor', color:'black' },
    {name: 'Commercials: swap dealers', color: 'grey'},
    {name: 'Non-commercial: managed money', color: 'red'},
    {name: 'Non-commercial: others', color: 'orange'},
    {name: 'Traders',  yAxis:1},
  ]
});


var disaggregated_spread_chart = Highcharts.chart('disaggregated-spread-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: true
  },
  title: {
      text: 'Disaggregated - spread',
  },
  xAxis: {
    type: 'datetime',
    crosshair:true
  },
  yAxis:[{
    title:'Long-Short',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Commercials: swap dealers', color: 'grey'},
    {name: 'Non-commercial: managed money', color: 'red'},
    {name: 'Non-commercial: others', color: 'orange'},
    {name: 'traders: swap dealers',  yAxis:1},
    {name: 'traders: managed money',  yAxis:1},
    {name: 'traders: others',  yAxis:1},
  ]
});

//financials chart

var financials_futures_chart = Highcharts.chart('financials-futures-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: true
  },
  title: {
      text: 'Financials - Futures',
  },
  xAxis: {
    type: 'datetime',
    crosshair: true
  },
  yAxis:[{
    title:'Long-Short',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Dealer/Intermediary', color:'grey' },
    {name: 'Asset Manager/Institutional', color: 'blue'},
    {name: 'Leveraged Funds', color: 'red'},
    {name: 'Other Reportables', color: 'orange'},
    {name: 'Traders',  yAxis:1},
  ]
});

var financials_option_chart = Highcharts.chart('financials-option-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: true
  },
  title: {
      text: 'Financials - Option',
  },
  xAxis: {
    type: 'datetime',
    crosshair:true
  },
  yAxis:[{
    title:'Long-Short',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Dealer/Intermediary', color:'grey' },
    {name: 'Asset Manager/Institutional', color: 'blue'},
    {name: 'Leveraged Funds', color: 'red'},
    {name: 'Other Reportables', color: 'orange'},
    {name: 'Traders',  yAxis:1},
  ]
});


var financials_spread_chart = Highcharts.chart('financials-spread-chart', {
  credits: {
    enabled: false
  },
  chart:{
    panning: true
  },
  title: {
      text: 'Financials - spread',
  },
  xAxis: {
    type: 'datetime',
    crosshair:true
  },
  yAxis:[{
    title:'Long-Short',
    height: '80%'
  },{
    title:'Traders',
    top:'80%',
    height:'20%'
  }],
  tooltip: {
    shared:true
  },
  plotOptions: {
    series: {
        states: {
          hover: {
            enabled: false
          },
          inactive: {
            opacity: 1
          }
        },
        marker: {
            enabled: false,
            states: {
                hover: {
                    enabled: false
                }
            }
        }
    },
  },
  series: [
    {name: 'Dealer/Intermediary', color:'grey' },
    {name: 'Asset Manager/Institutional', color: 'orange'},
    {name: 'Leveraged Funds', color: 'red'},
    {name: 'Other Reportables', color: 'orange'},
    {name: 'Traders-dealer',  yAxis:1},
    {name: 'Traders-institutional',  yAxis:1},
    {name: 'Traders-funds',  yAxis:1},
    {name: 'Traders-others',  yAxis:1},
  ]
});


var load_data = function(sector, name) {
  $('#name').text(name);
  $.get( $(location).attr('href')+`?action=legacy&params=${sector},${name}`, function( res ) {
      let futures = res.futures;
      let option = res.option;

      let commercial = [];
      let non_commercial = [];
      let unknown = [];
      let traders= [];
      for (val of futures){
        commercial.push([val[0],val[2]]);
        non_commercial.push([val[0],val[1]]);
        unknown.push([val[0],val[3]]);
        traders.push([val[0], val[4]]);
      };
      legacy_futures_chart.series[0].update({
        'data': commercial
      }, false);
      legacy_futures_chart.series[1].update({
        'data': non_commercial
      }, false);
      legacy_futures_chart.series[2].update({
        'data': unknown
      }, false);
      legacy_futures_chart.series[3].update({
        'data': traders
      }, false);

      legacy_futures_chart.redraw();

      commercial = [];
      non_commercial = [];
      unknown = [];
      traders= [];
      for (val of option){
        commercial.push([val[0],val[2]]);
        non_commercial.push([val[0],val[1]]);
        unknown.push([val[0],val[3]]);
        traders.push([val[0], val[4]]);
      };
      legacy_option_chart.series[0].update({
        'data': commercial
      }, false);
      legacy_option_chart.series[1].update({
        'data': non_commercial
      }, false);
      legacy_option_chart.series[2].update({
        'data': unknown
      }, false);
      legacy_option_chart.series[3].update({
        'data': traders
      }, false);

      legacy_option_chart.redraw();

      legacy_spread_chart.series[0].update({
        'data': res.spread_position
      },false);
      legacy_spread_chart.series[1].update({
        'data': res.spread_traders
      },false);
      legacy_spread_chart.redraw();

  });

  if (['grains','energies','metals','softs','livestocks'].includes(sector)){
    $('#disaggregated').show();
      $('#financials').hide();
    $.get( $(location).attr('href')+`?action=disaggregated&params=${sector},${name}`, function( res ) {
      let futures = res.futures;
      let option = res.option;
      let spread = res.spread;

      let producer = [];
      let swap = [];
      let funds = [];
      let others = [];
      let traders= [];
      for (val of futures){
        producer.push([val[0],val[1]]);
        swap.push([val[0],val[2]]);
        funds.push([val[0],val[3]]);
        others.push([val[0],val[4]]);
        traders.push([val[0], val[5]]);
      };
      disaggregated_futures_chart.series[0].update({
        'data': producer
      }, false);
      disaggregated_futures_chart.series[1].update({
        'data': swap
      }, false);
      disaggregated_futures_chart.series[2].update({
        'data': funds
      }, false);
      disaggregated_futures_chart.series[3].update({
        'data': others
      }, false);
      disaggregated_futures_chart.series[4].update({
        'data': traders
      }, false);

      disaggregated_futures_chart.redraw();

      producer = [];
      swap = [];
      funds = [];
      others = [];
      traders= [];
      for (val of option){
        producer.push([val[0],val[1]]);
        swap.push([val[0],val[2]]);
        funds.push([val[0],val[3]]);
        others.push([val[0],val[4]]);
        traders.push([val[0], val[5]]);
      };
      disaggregated_option_chart.series[0].update({
        'data': producer
      }, false);
      disaggregated_option_chart.series[1].update({
        'data': swap
      }, false);
      disaggregated_option_chart.series[2].update({
        'data': funds
      }, false);
      disaggregated_option_chart.series[3].update({
        'data': others
      }, false);
      disaggregated_option_chart.series[4].update({
        'data': traders
      }, false);

      disaggregated_option_chart.redraw();

      // spread
      swap = [];
      funds = [];
      others = [];
      traders_swap = [];
      traders_funds = [];
      traders_others = [];
      for (val of spread){
        swap.push([val[0],val[1]]);
        funds.push([val[0],val[2]]);
        others.push([val[0],val[3]]);
        traders_swap.push([val[0], val[4]]);
        traders_funds.push([val[0], val[5]]);
        traders_others.push([val[0], val[6]]);
      }
      disaggregated_spread_chart.series[0].update({
        'data': swap
      }, false);
      disaggregated_spread_chart.series[1].update({
        'data': funds
      }, false);
      disaggregated_spread_chart.series[2].update({
        'data': others
      }, false);
      disaggregated_spread_chart.series[3].update({
        'data': traders_swap
      }, false);
      disaggregated_spread_chart.series[4].update({
        'data': traders_funds
      }, false);
      disaggregated_spread_chart.series[5].update({
        'data': traders_others
      }, false);

      disaggregated_spread_chart.redraw();
    
    });
  } else if (['currencies','indices','rates'].includes(sector)){
    $('#disaggregated').hide();
    $('#financials').show();
    $.get( $(location).attr('href')+`?action=financials&params=${sector},${name}`, function( res ) {
      
      let futures = res.futures;
      let option = res.option;
      let spread = res.spread;

      let dealers = [];
      let institutions = [];
      let funds = [];
      let others = [];
      let traders= [];
      for (val of futures){
        dealers.push([val[0],val[1]]);
        institutions.push([val[0],val[2]]);
        funds.push([val[0],val[3]]);
        others.push([val[0],val[4]]);
        traders.push([val[0], val[5]]);
      };
      financials_futures_chart.series[0].update({
        'data': dealers
      }, false);
      financials_futures_chart.series[1].update({
        'data': institutions
      }, false);
      financials_futures_chart.series[2].update({
        'data': funds
      }, false);
      financials_futures_chart.series[3].update({
        'data': others
      }, false);
      financials_futures_chart.series[4].update({
        'data': traders
      }, false);

      financials_futures_chart.redraw();

      dealers = [];
      institutions = [];
      funds = [];
      others = [];
      traders= [];
      for (val of option){
        dealers.push([val[0],val[1]]);
        institutions.push([val[0],val[2]]);
        funds.push([val[0],val[3]]);
        others.push([val[0],val[4]]);
        traders.push([val[0], val[5]]);
      };
      financials_option_chart.series[0].update({
        'data': dealers
      }, false);
      financials_option_chart.series[1].update({
        'data': institutions
      }, false);
      financials_option_chart.series[2].update({
        'data': funds
      }, false);
      financials_option_chart.series[3].update({
        'data': others
      }, false);
      financials_option_chart.series[4].update({
        'data': traders
      }, false);

      financials_option_chart.redraw();

      // spread
      dealers = [];
      institutions = [];
      funds = [];
      others = [];
      traders_dealers = [];
      traders_institutions = [];
      traders_funds = [];
      traders_others = [];
      for (val of spread){
        dealers.push([val[0],val[1]]);
        institutions.push([val[0],val[2]]);
        funds.push([val[0],val[3]]);
        others.push([val[0],val[4]]);
        traders_dealers.push([val[0], val[5]]);
        traders_institutions.push([val[0], val[6]]);
        traders_funds.push([val[0], val[7]]);
        traders_others.push([val[0], val[8]]);
      }
      financials_spread_chart.series[0].update({
        'data': dealers
      }, false);
      financials_spread_chart.series[1].update({
        'data': institutions
      }, false);
      financials_spread_chart.series[2].update({
        'data': funds
      }, false);
      financials_spread_chart.series[3].update({
        'data': others
      }, false);
      financials_spread_chart.series[4].update({
        'data': traders_dealers
      }, false);
      financials_spread_chart.series[5].update({
        'data': traders_institutions
      }, false);
      financials_spread_chart.series[6].update({
        'data': traders_funds
      }, false);
      financials_spread_chart.series[7].update({
        'data': traders_others
      }, false);

      financials_spread_chart.redraw();
    
    });
  };

};

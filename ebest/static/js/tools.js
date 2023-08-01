//메세지 로그
var logs = [];
const log = function(msg){
    let text = `[${gettime().toLocaleString()}] ${msg}`
    logs.push(text);
    logs = logs.slice(-6);
    $('#log').html(logs.join('<br/>'));
}


//시계
const gettime = function(){
    ctime = new Date();
    ktime = ctime.getTime() + (ctime.getTimezoneOffset() + 540)*60*1000;
    return new Date(ktime);
}


/* 날짜 형식 
  이베스트 api 에서 들어오는 날짜형식이 YYYYmmdd 와 HHMMSS 
  이기 때문에 일관성을 위해 다른 모든 곳에서도 이 형식으로 다룬다. 
*/
const datetime = {
  'pastday': function(daysbefore){
    let s = new Date();
    let date = new Date(s.getTime() - s.getTimezoneOffset()*60*1000 - daysbefore*24*60*60*1000) ;
    return this.toString(date);
  },
  'toString': function(dateobj){ 
    let arr = dateobj.toISOString().slice(0,19)
                                .replaceAll('-','')
                                .replaceAll(':','')
                                .split('T');
    return { 'date':arr[0], 'time': arr[1] }
  },
  'today': function(){
    let s = new Date();
    let date = new Date(s.getTime() - s.getTimezoneOffset()*60*1000);
    return this.toString(date);
  },
  'timestamp': function(date, time){
    let year = date.slice(0,4);
    let month = parseInt(date.slice(4,6))-1;
    let day = date.slice(6,8);
    if (time == null) {
      return Date.UTC(year, month, day);
    } else {
      let hour = time.slice(0,2);
      let minute = time.slice(2,4);
      let second = time.slice(4,6);
      return Date.UTC(year, month, day, hour, minute, second);
    }
  },
}
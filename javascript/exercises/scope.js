function Forecast(day) {
  this.day = day;
  this.getWeatherData= setForecast;
}

function setForecast() {
  this.temp = Math.floor(Math.random()*90);
  this.precip = Math.floow(Math.random()*100);
}

let days = [
  new Forecast('Friday'),
  new Forecast('Saturday'),
  new Forecast('Sundary'),
];


for (let i = 0; i < days.length; i++) {
  let m = movies[i]
  console.log('');
  console.log(m);
  console.log('');
}


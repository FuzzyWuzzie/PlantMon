var hsv2rgb = function(h, s, v) {
  // adapted from http://schinckel.net/2012/01/10/hsv-to-rgb-in-javascript/
  var rgb, i, data = [];
  if (s === 0) {
	rgb = [v,v,v];
  } else {
	h = h / 60;
	i = Math.floor(h);
	data = [v*(1-s), v*(1-s*(h-i)), v*(1-s*(1-(h-i)))];
	switch(i) {
	  case 0:
		rgb = [v, data[2], data[0]];
		break;
	  case 1:
		rgb = [data[1], v, data[0]];
		break;
	  case 2:
		rgb = [data[0], v, data[2]];
		break;
	  case 3:
		rgb = [data[0], data[1], v];
		break;
	  case 4:
		rgb = [data[2], data[0], v];
		break;
	  default:
		rgb = [v, data[0], data[1]];
		break;
	}
  }
  return '#' + rgb.map(function(x){
	return ("0" + Math.round(x*255).toString(16)).slice(-2);
  }).join('');
};

var sensor0LineChart, sensor0Gauge;
var sensor1LineChart, sensor1Gauge;
var sensor2LineChart, sensor2Gauge;
var sensor3LineChart, sensor3Gauge;
var sensor4LineChart, sensor4Gauge;
//var sensor5LineChart, sensor5Gauge;

function updateAlarms() {
	$.ajax({
		url: '/alarms',
		dataType: 'json',
		success: function(data, textStatus, jqXHR) {
			$("#sensor-0-alarm").toggleClass("danger", data[0]);
			$("#sensor-1-alarm").toggleClass("danger", data[1]);
			$("#sensor-2-alarm").toggleClass("danger", data[2]);
			$("#sensor-3-alarm").toggleClass("danger", data[3]);
			$("#sensor-4-alarm").toggleClass("danger", data[4]);
			//$("#sensor-5-alarm").toggleClass("danger", data[5]);

			$("#sensor-0-alarm").toggleClass("success", !data[0]);
			$("#sensor-1-alarm").toggleClass("success", !data[1]);
			$("#sensor-2-alarm").toggleClass("success", !data[2]);
			$("#sensor-3-alarm").toggleClass("success", !data[3]);
			$("#sensor-4-alarm").toggleClass("success", !data[4]);
			//$("#sensor-5-alarm").toggleClass("success", !data[5]);
		},
		error: function(data, textStatus, jqXHR) {
			console.log(data);
		}
	});

	setTimeout(updateGauges, 1000);
}

function updateGauges() {
	$.ajax({
		url: '/sensors',
		dataType: 'json',
		success: function(data, textStatus, jqXHR) {
			sensor0Gauge.series[0].setData([data.values[0]]);
			sensor1Gauge.series[0].setData([data.values[1]]);
			sensor2Gauge.series[0].setData([data.values[2]]);
			sensor3Gauge.series[0].setData([data.values[3]]);
			sensor4Gauge.series[0].setData([data.values[4]]);
			//sensor5Gauge.series[0].setData([data.values[5]]);
		},
		error: function(data, textStatus, jqXHR) {
			console.log(data);
		}
	});

	setTimeout(updateGauges, 1000);
}

function updateSensors() {
	$.ajax({
		url: '/history',
		dataType: 'json',
		data: {
			sensor: -1, // get all the sensors at once
			dt: 2 * 24 * 3600 // two days of data max
		},
		success: function(data, textStatus, jqXHR) {
			sensor0LineChart.series[0].setData(data[0]);
			sensor1LineChart.series[0].setData(data[1]);
			sensor2LineChart.series[0].setData(data[2]);
			sensor3LineChart.series[0].setData(data[3]);
			sensor4LineChart.series[0].setData(data[4]);
			//sensor5LineChart.series[0].setData(data[5]);
		},
		error: function(data, textStatus, jqXHR) {
			console.log(data);
		}
	});

	setTimeout(updateSensors, 10000);
}

$(document).ready(function() {
	var gaugeOptions = {
		chart: {
			type: 'solidgauge',
		},
		title: null,
		pane: {
			center: ['100%', '100%'],
			size: '200%',
			startAngle: -90,
			endAngle: 0,
			background: {
				backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
				innerRadius: '60%',
				outerRadius: '100%',
				shape: 'arc'
			}
		},
		yAxis: {
			min: 0,
			max: 100,
			title: null,
			stops: [
				[0.1, '#DF5353'],
				[0.5, '#DDDF0D'],
				[0.9, '#55BF3B']
			],
		},
		tooltip: {
			enabled: false
		},
		series: [{
			name: 'Water Level',
			data: [0],
			dataLabels: {
				format: '<div style="text-align:center"><span style="font-size:25px;">{y:.0f}</span><span style="font-size:20px">%</span></div>',
				y: 5,
				borderWidth: 0,
				useHTML: true
			}
		}],
		credits: {
			enabled: false
		},
	};

	var lineOptions = {
		chart: {
			zoomType: 'x',
			type: 'spline'
		},
		title: null,
		xAxis: {
			type: 'datetime',
			title: {
				text: 'Date'
			}
		},
		yAxis: {
			title: {
				text: 'Water Level (%)'
			},
		},
		legend: {
			enabled: false
		},
		tooltip: {
			headerFormat: '<b>{series.name}</b><br>',
			pointFormat: '{point.x:%Y-%m-%d %l:%M:%S %P}: {point.y:.2f}%'
		},
		series: [{
			name: 'Water Level',
			data: []
		}],
		credits: {
			enabled: false
		},
	};

	sensor0Gauge = new Highcharts.Chart(Highcharts.merge(gaugeOptions, {
		chart: {
			renderTo: 'sensor-0-gauge-container'
		}
	}));

	sensor0LineChart = new Highcharts.Chart(Highcharts.merge(lineOptions, {
		chart: {
			renderTo: 'sensor-0-line-container'
		}
	}));

	sensor1Gauge = new Highcharts.Chart(Highcharts.merge(gaugeOptions, {
		chart: {
			renderTo: 'sensor-1-gauge-container'
		}
	}));

	sensor1LineChart = new Highcharts.Chart(Highcharts.merge(lineOptions, {
		chart: {
			renderTo: 'sensor-1-line-container'
		}
	}));

	sensor2Gauge = new Highcharts.Chart(Highcharts.merge(gaugeOptions, {
		chart: {
			renderTo: 'sensor-2-gauge-container'
		}
	}));

	sensor2LineChart = new Highcharts.Chart(Highcharts.merge(lineOptions, {
		chart: {
			renderTo: 'sensor-2-line-container'
		}
	}));

	sensor3Gauge = new Highcharts.Chart(Highcharts.merge(gaugeOptions, {
		chart: {
			renderTo: 'sensor-3-gauge-container'
		}
	}));

	sensor3LineChart = new Highcharts.Chart(Highcharts.merge(lineOptions, {
		chart: {
			renderTo: 'sensor-3-line-container'
		}
	}));

	sensor4Gauge = new Highcharts.Chart(Highcharts.merge(gaugeOptions, {
		chart: {
			renderTo: 'sensor-4-gauge-container',
			events: {
				load: updateGauges()
			}
		}
	}));

	sensor4LineChart = new Highcharts.Chart(Highcharts.merge(lineOptions, {
		chart: {
			renderTo: 'sensor-4-line-container',
			events: {
				load: updateSensors()
			}
		}
	}));

	updateAlarms();
});
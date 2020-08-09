var minRSTChart;
var hourRSTChart;
var threeHourRSTChart;
var minPLChart;
var hourPLChart;
var threeHourPLChart;
var autoRefresh = false;
var functionTimer;

function buildPLChart(elementName, color, pingTimestamp, packetLoss) {
    var ctx = document.getElementById(elementName).getContext("2d");
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: pingTimestamp,
            datasets: [{
                borderColor: color,
                fill: false,
                label: "Ping Packet Loss",
                data: packetLoss,
            }]
        },
        options: {
            tooltips: {
                displayColors: false,
                callbacks: {
                    label: function (TooltipItem, object){
                        return TooltipItem['value'] + '% (Rolling Average)'
                    }
                }
            },
            legend: {
                display: false
            },
            scales: {
                x: {
                    display: true,
                    gridLines: {
                        display: false
                    }
                },
                y: {
                    gridLines: {
                        display: false
                    },
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function (value, index, values) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
    return chart;
}

function buildRSTChart(elementName, color, pingTimestamp, RST) {
    var ctx = document.getElementById(elementName).getContext("2d");
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: pingTimestamp,
            datasets: [{
                label: "Response Time",
                data: RST,
                backgroundColor: color
            }]
        },
        options: {
            tooltips: {
                displayColors: false,
                callbacks: {
                    label: function (TooltipItem, object){
                        return TooltipItem['value'] + 'ms'
                    }
                }
            },
            legend: {
                display: false
            },
            scales: {
                x: {

                    display: true,
                    gridLines: {
                        display: false
                    }
                },
                y: {
                    gridLines: {
                        display: false
                    },
                    ticks: {
                        beginAtZero: true,
                        callback: function (value, index, values) {
                            return value + 'ms';
                        }
                    }
                }
            }
        }
    });
    return chart;
}

function createGraphs() {
    $.ajax({
    url: '/latest.json',
    dataType: 'json',
    success: function(data) {
        $('#minuteRSTAVG').text(data['min_RST_AVG'] + 'ms')
        $('#hourRSTAVG').text(data['hour_RST_AVG'] + 'ms')
        $('#threeHourRSTAVG').text(data['threeHour_RST_AVG'] + 'ms')
        $('#minPLAVG').text(data['min_PL_AVG'] + '%')
        $('#hourPLAVG').text(data['hour_PL_AVG'] + '%')
        $('#threeHourPLAVG').text(data['threeHour_PL_AVG'] + '%')
        minRSTChart = buildRSTChart('minuteRST', '#4caf50', data['minuteTimestamp'], data['minuteRTC'])
        hourRSTChart = buildRSTChart('hourRST', '#fcba03', data['hourTimestamp'], data['hourRTC'])
        threeHourRSTChart = buildRSTChart('threeHourRST', '#00bcd4', data['threeHourTimestamp'], data['threeHourRTC'])
        minPLChart = buildPLChart('minutePL', '#4caf50', data['minuteTimestamp'], data['minutePL'])
        hourPLChart = buildPLChart('hourPL', '#fcba03', data['hourTimestamp'], data['hourPL'])
        threeHourPLChart = buildPLChart('threeHourPL', '#00bcd4', data['threeHourTimestamp'], data['threeHourPL'])
    }
    })
}

function updateGraph(chart, timestamp, data){
    chart.data.labels = timestamp
    chart.data.datasets[0].data = data
    chart.update();
}

function updateGraphs() {
    $.ajax({
    url: '/latest.json',
    dataType: 'json',
    success: function(data) {
        $('#minuteRSTAVG').text(data['min_RST_AVG'] + 'ms')
        $('#hourRSTAVG').text(data['hour_RST_AVG'] + 'ms')
        $('#threeHourRSTAVG').text(data['threeHour_RST_AVG'] + 'ms')
        $('#minPLAVG').text(data['min_PL_AVG'] + '%')
        $('#hourPLAVG').text(data['hour_PL_AVG'] + '%')
        $('#threeHourPLAVG').text(data['threeHour_PL_AVG'] + '%')
        updateGraph(minRSTChart, data['minuteTimestamp'], data['minuteRTC'])
        updateGraph(hourRSTChart, data['hourTimestamp'], data['hourRTC'])
        updateGraph(threeHourRSTChart, data['threeHourTimestamp'], data['threeHourRTC'])
        updateGraph(minPLChart, data['minuteTimestamp'], data['minutePL'])
        updateGraph(hourPLChart, data['hourTimestamp'], data['hourPL'])
        updateGraph(threeHourPLChart, data['threeHourTimestamp'], data['threeHourPL'])
    }
    })
}

$(document).ready(function() {
    createGraphs();
});

$('#autoRefreshButton').click(function(){
autoRefresh = !autoRefresh
if(autoRefresh){
    updateGraphs()
    functionTimer = setInterval(updateGraphs, 1000)
    $('#autoRefreshButton').removeClass('btn-outline-success').addClass('btn-success')
}else{
    $('#autoRefreshButton').removeClass('btn-success').addClass('btn-outline-success')
    clearInterval(functionTimer)
}
})

$('#refreshButton').click(function(){
    $('#refreshButton').addClass('fa-spin')
    updateGraphs()
    $('#refreshButton').removeClass('fa-spin')
});
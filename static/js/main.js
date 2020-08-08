function buildPLChart(elementName, color, pingTimestamp, packetLoss) {
    var ctx = document.getElementById(elementName).getContext("2d");
    new Chart(ctx, {
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
                xAxes: [{
                    display: true,
                    gridLines: {
                        display: false
                    }
                }],
                yAxes: [{
                    gridLines: {
                        display: false
                    },
                    ticks: {
                        callback: function (value, index, values) {
                            return value + '%';
                        }
                    }
                }]
            }
        }
    });
}

function buildRSTChart(elementName, color, pingTimestamp, RST) {
    var ctx = document.getElementById(elementName).getContext("2d");
    new Chart(ctx, {
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
                xAxes: [{

                    display: true,
                    gridLines: {
                        display: false
                    }
                }],
                yAxes: [{
                    gridLines: {
                        display: false
                    },
                    ticks: {
                        beginAtZero: true,
                        callback: function (value, index, values) {
                            return value + 'ms';
                        }
                    }
                }]
            }
        }
    });
}

$( document ).ready(function() {
    $.ajax({
    url: '/latest.json',
    dataType: 'json',
    success: function(data) {
        $('#minuteRSTAVG').text(data['min_RST_AVG'] + 'ms')
        $('#hourRSTAVG').text(data['hour_RST_AVG'] + 'ms')
        $('#threeHourRSTAVG').text(data['threeHour_RST_AVG'] + 'ms')
        buildRSTChart('minuteRST', '#4caf50', data['minuteTimestamp'], data['minuteRTC'])
        buildRSTChart('hourRST', '#fcba03', data['hourTimestamp'], data['hourRTC'])
        buildRSTChart('threeHourRST', '#00bcd4', data['threeHourTimestamp'], data['threeHourRTC'])
        $('#minPLAVG').text(data['min_PL_AVG'] + '%')
        $('#hourPLAVG').text(data['hour_PL_AVG'] + '%')
        $('#threeHourPLAVG').text(data['threeHour_PL_AVG'] + '%')
        buildPLChart('minutePL', '#4caf50', data['minuteTimestamp'], data['minutePL'])
        buildPLChart('hourPL', '#fcba03', data['hourTimestamp'], data['hourPL'])
        buildPLChart('threeHourPL', '#00bcd4', data['threeHourTimestamp'], data['threeHourPL'])
    }
    })
});
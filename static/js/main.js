function buildPLChart(elementName, color, pingTimestamp, packetLoss) {
    var ctx = document.getElementById(elementName).getContext("2d");
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: pingTimestamp,
            datasets: [{
                borderColor: color,
                fill: false,
                label: "Ping Time",
                data: packetLoss,
            }]
        },
        options: {
            legend: {
                display: false
            },
            scales: {
                xAxes: [{
                    display: false,
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
                label: "Ping Response Time",
                data: RST,
                backgroundColor: color
            }]
        },
        options: {
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
        buildRSTChart('minuteRST', '#fcba03', data['minuteTimestamp'], data['minuteRTC'])
        buildRSTChart('hourRST', '#fcba03', data['hourTimestamp'], data['hourRTC'])
        buildRSTChart('threeHourRST', '#fcba03', data['threeHourTimestamp'], data['threeHourRTC'])
        $('#minPLAVG').text(data['minutePL'][data['minutePL'].length - 1] + '%')
        $('#hourPLAVG').text(data['hourPL'][data['hourPL'].length - 1] + '%')
        $('#threeHourPLAVG').text(data['threeHourPL'][data['threeHourPL'].length - 1] + '%')
        buildPLChart('minutePL', '#fcba03', data['minuteTimestamp'], data['minutePL'])
        buildPLChart('hourPL', '#fcba03', data['hourTimestamp'], data['hourPL'])
        buildPLChart('threeHourPL', '#fcba03', data['threeHourTimestamp'], data['threeHourPL'])
    }
    })
});
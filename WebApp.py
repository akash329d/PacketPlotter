from flask import render_template, Flask, json, make_response
import threading
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import pingparsing
import sqlite3
import gzip
import numpy as np

# TODO: Code Cleanup, Offset Charts (Based On Data Collected), Figure out better averaging (right now the data doesn't shift correct when not collecting, will need to figure out better visualization for that), also AJAX for sending table data, instead of HTML Template.
# TODO: ADD PACKET LOSS PERCENTAGES


app = Flask(__name__, template_folder="static")


def distance(a, b):
    return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def distancePointLine(linea, lineb, a):
    if linea == lineb:
        return distance(a, linea)
    x_diff = linea[0] - lineb[0]
    y_diff = linea[1] - lineb[1]
    num = abs(y_diff*a[0] - x_diff * a[1] + linea[0] * lineb[1] - linea[1] * lineb[0])
    den = np.sqrt(y_diff ** 2 + x_diff ** 2)
    return num / den


def douglasPeucker(xpoints, ypoints, epsilon):
    maxDistance, index = 0.0, 0
    for x in range(1, len(xpoints) - 1):
        d = distancePointLine([xpoints[0], ypoints[0]], [xpoints[-1], ypoints[-1]], [xpoints[x], ypoints[x]])
        if d > maxDistance:
            index = x
            maxDistance = d
    if maxDistance > epsilon:
        leftResultsX, leftResultsY = douglasPeucker(xpoints[:index], ypoints[:index], epsilon)
        rightResultsX, rightResultsY = douglasPeucker(xpoints[index:], ypoints[index:], epsilon)
        resultsx, resultsy = leftResultsX + rightResultsX, leftResultsY + rightResultsY
    else:
        resultsx = [xpoints[0], xpoints[-1]]
        resultsy = [ypoints[0], ypoints[-1]]

    return resultsx, resultsy


def doPing():
    ping_parser = pingparsing.PingParsing()
    transmitter = pingparsing.PingTransmitter()
    transmitter.destination = "8.8.8.8"
    transmitter.count = 1
    transmitter.timeout = "200ms"
    result = transmitter.ping()
    return ping_parser.parse(result).as_dict()


def timerPing():
    db = sqlite3.connect("pings.db")
    pingData = doPing()
    pingData["timestamp"] = time.time()
    if pingData["packet_receive"] == 0:
        pingData["rtt_avg"] = 0
    con = db.cursor()
    con.execute("""INSERT INTO pings VALUES (?, ?, ?, ?)"""
                , (pingData["timestamp"], pingData["destination"], pingData["packet_receive"], pingData["rtt_avg"]))
    db.commit()
    db.close()


def nonZeroMean(arr):
    total = 0
    count = 0
    for x in arr:
        if x != 0:
            total, count = total + x, count + 1
    return total / count


def calculateArray(data, timeLimit, decimation):
    timeArr, RTCArr, PLArr = [], [], []
    totalPackets, packetsReceived = 0, 0
    startingIndex = np.searchsorted(list(zip(*data))[0], timeLimit, side='right')
    secondsToPad = int(data[startingIndex][0] - timeLimit)

    for ping in data[startingIndex:]:
        totalPackets += 1
        packetsReceived += ping[2]
        RTCArr.append(ping[3])
        timeArr.append(round(ping[0] - timeLimit))
        PLArr.append(round((totalPackets - packetsReceived) * 100 / totalPackets, 2))

    missing_indices = sorted(set(range(round(data[startingIndex][0] - timeLimit), round(data[-1][0] - timeLimit + 1)))
                             .difference(timeArr))
    for missingIndex in missing_indices:
        timeArr.insert(missingIndex - 1, missingIndex)
        RTCArr.insert(missingIndex - 1, 0)
        PLArr.insert(missingIndex - 1, 0.0)

    timeArr = (list(range(1, secondsToPad + 1)) + timeArr)[::decimation]
    RTCArr = ([0] * secondsToPad + RTCArr)[::decimation]
    PLArr = ([0.0] * secondsToPad + PLArr)[::decimation]
    return timeArr, RTCArr, PLArr


@app.route("/latest.json")
def dataResponse():
    db = sqlite3.connect("pings.db")
    last3Hour = time.time() - 3 * 60 * 60
    lastHour = last3Hour + 2 * 60 * 60
    lastMinute = lastHour + 59 * 60
    cursor = db.cursor()
    cursor.execute("""SELECT * from pings WHERE timestamp > ? ORDER BY timestamp ASC""", (last3Hour,))
    data = cursor.fetchall()
    cursor.close()
    threeHourTimestamp, threeHourRTC, threeHourPL = calculateArray(data, last3Hour, 1)
    hourPingTimestamp, hourRTC, hourPL = calculateArray(data, lastHour, 1)
    print(threeHourRTC)
    print(hourRTC)
    minPingTimestamp, minRTC, minPL = calculateArray(data, lastMinute, 1)
    toReturn = {"min_RST_AVG": round(nonZeroMean(minRTC), 2),
                "threeHour_RST_AVG": round(nonZeroMean(threeHourRTC), 2),
                "hour_RST_AVG": round(nonZeroMean(hourRTC), 2),
                "threeHourRTC": threeHourRTC,
                "threeHourPL": threeHourPL,
                "threeHourTimestamp": threeHourTimestamp,
                "hourRTC": hourRTC,
                "hourPL": hourPL,
                "hourTimestamp": hourPingTimestamp,
                "minuteRTC": minRTC,
                "minutePL": minPL,
                "minuteTimestamp": minPingTimestamp}
    compressedReturn = gzip.compress(json.dumps(toReturn).encode('utf8'))
    response = make_response(compressedReturn)
    response.headers['Content-length'] = len(compressedReturn)
    response.headers['Content-Encoding'] = 'gzip'
    return response


@app.route("/")
def dashboard():
    return render_template('chart.html')


if __name__ == "__main__":
    db = sqlite3.connect("pings.db")
    con = db.cursor()
    con.execute("""CREATE TABLE IF NOT EXISTS pings (
    timestamp REAL PRIMARY KEY,
    destination TEXT NOT NULL,
    packet_received INTEGER NOT NULL,
    RTT INTEGER NOT NULL)""")
    db.commit()
    db.close()
    sched = BlockingScheduler()
    sched.add_job(timerPing, 'cron', second='*')
    threading.Thread(target=app.run, daemon=True, args=()).start()
    sched.start()

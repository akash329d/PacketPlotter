from flask import render_template, Flask, json, make_response
import threading
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import pingparsing
from datetime import datetime
import sqlite3
import gzip
import numpy as np

app = Flask(__name__, template_folder="static")


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
        if x is not None and x != 0:
            total, count = total + x, count + 1
    return total / count


def averageArray(array, sliceSize, threshold):
    if sliceSize == 1:
        return array

    def averageHelper(i):
        total, count, noneCount = 0, 0, 0
        for x in array[i: i + sliceSize]:
            if x is not None:
                total += x
                count += 1
            else:
                noneCount += 1
        if noneCount / sliceSize > .5:
            return None
        if total == 0 or count == 0:
            total, count = 0, 1
        toReturn = round(total / count, 2)
        return 0 if toReturn < threshold else toReturn

    return [averageHelper(i) for i in range(0, len(array), sliceSize)]


def calculateArray(data, timeLimit, sliceSize, thresholdRTC):
    timeArr, RTCArr, PLArr = [], [], []
    totalPackets, packetsReceived = 0, 0
    startingIndex = np.searchsorted(list(zip(*data))[0], timeLimit, side='right')
    secondsToPad = int(data[startingIndex][0] - timeLimit)
    indexTracker = []
    for ping in data[startingIndex:]:
        totalPackets += 1
        packetsReceived += ping[2]
        RTCArr.append(ping[3])
        indexTracker.append(round(ping[0] - timeLimit))
        timeArr.append(ping[0])
        PLArr.append(round((totalPackets - packetsReceived) * 100 / totalPackets, 2))

    missingIndices = sorted(set(range(round(data[startingIndex][0] - timeLimit), round(data[-1][0] - timeLimit + 1)))
                            .difference(indexTracker))
    for missingIndex in missingIndices:
        timeArr.insert(missingIndex - 1 - indexTracker[0], missingIndex + timeLimit)
        RTCArr.insert(missingIndex - 1 - indexTracker[0], 0)
        PLArr.insert(missingIndex - 1 - indexTracker[0], None)

    PLAvg = PLArr[-1]
    timeArr = averageArray(timeArr + [x + data[-1][0] for x in range(1, secondsToPad + 1)], sliceSize, 0)
    RTCArr = averageArray((RTCArr + [0] * secondsToPad), sliceSize, thresholdRTC)
    PLArr = averageArray((PLArr + [0] * secondsToPad), sliceSize, 0)
    timeArr = [datetime.fromtimestamp(t).strftime('%I:%M:%S%p') for t in timeArr]
    return timeArr, RTCArr, PLArr, PLAvg


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
    threeHourTimestamp, threeHourRTC, threeHourPL, threeHourPLAvg = calculateArray(data, last3Hour, 60, 3.5)
    hourPingTimestamp, hourRTC, hourPL, hourPLAvg = calculateArray(data, lastHour, 60, 3.5)
    minPingTimestamp, minRTC, minPL, minPLAvg = calculateArray(data, lastMinute, 1, 3.5)
    toReturn = {"min_RST_AVG": round(nonZeroMean(minRTC), 2),
                "threeHour_RST_AVG": round(nonZeroMean(threeHourRTC), 2),
                "hour_RST_AVG": round(nonZeroMean(hourRTC), 2),
                "min_PL_AVG": minPLAvg,
                "threeHour_PL_AVG": threeHourPLAvg,
                "hour_PL_AVG": hourPLAvg,
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

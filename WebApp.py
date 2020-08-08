from flask import render_template, Flask, json, make_response
import threading
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import pingparsing
import sqlite3
import gzip


# TODO: Code Cleanup, Offset Charts (Based On Data Collected), Figure out better averaging (right now the data doesn't shift correct when not collecting, will need to figure out better visualization for that), also AJAX for sending table data, instead of HTML Template.
# TODO: ADD PACKET LOSS PERCENTAGES

def doPing():
    ping_parser = pingparsing.PingParsing()
    transmitter = pingparsing.PingTransmitter()
    transmitter.destination = "8.8.8.8"
    transmitter.count = 1
    transmitter.timeout = "200ms"
    result = transmitter.ping()
    return ping_parser.parse(result).as_dict()


app = Flask(__name__, template_folder="static")


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


def calculateArray(data, timeLimit, decimation):
    timeArr = []
    RTCArr = []
    PLArr = []
    totalPackets = 0
    packetsReceived = 0
    curIndex = len(data) - 1
    while data[curIndex][0] > timeLimit:
        curIndex -= 1
        if curIndex == 0:
            break
    curIndex += 1
    for ping in data[curIndex:]:
        totalPackets += 1
        packetsReceived += ping[2]
        RTCArr.append(ping[3])
        timeArr.append(round(ping[0] - timeLimit))
        PLArr.append(round((totalPackets - packetsReceived) * 100 / totalPackets, 2))
    return timeArr[::decimation], RTCArr[::decimation], PLArr[::decimation]


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
    minPingTimestamp, minRTC, minPL = calculateArray(data, lastMinute, 1)
    toReturn = {"min_RST_AVG": round(sum(minRTC) / len(minRTC), 2),
                "threeHour_RST_AVG": round(sum(threeHourRTC) / len(threeHourRTC), 2),
                "hour_RST_AVG": round(sum(hourRTC) / len(hourRTC), 2),
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

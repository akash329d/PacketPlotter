import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import os
import numpy as np
import pingparsing
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint, Flask

from pingplotter.utils import averageArray

dataCollection = Blueprint('dataCollection', __name__)
sched = BackgroundScheduler(daemon=True)

def calculateArray(data, timeLimit, sliceSize, thresholdRTC, missingDataThreshold):
    """Calculates the Timestamp Array, Response Time (RTC) Array,, Packet Loss (PL) Array and PL Average from
    an array of ping's. Only uses pings that are more recent than a specific timeLimit (unix timestamp). sliceSize
    determines how many samples should be generated. The thresholdRTC value determines when a RTC should be considered
    0 for a specific sample. missingDataThreshold determines the percentage of missing data required
    for a value to be returned as None for averaging. Additionally, if not enough data exists,
    pads the return samples with None values for graphing.
    Finally, gaps in the data are filled in with None values as well."""
    timeSet, timeArr, RTCArr, PLArr = set(), [], [], []
    totalPackets, packetsReceived = 0, 0
    startingIndex = np.searchsorted(list(zip(*data))[0], timeLimit, side='right')
    secondsToPad = int(data[startingIndex][0] - timeLimit)
    for ping in data[startingIndex:]:
        totalPackets += 1
        packetsReceived += ping[2]
        RTCArr.append(ping[3])
        timeSet.add(round(ping[0]))
        PLArr.append(round((totalPackets - packetsReceived) * 100 / totalPackets, 2))

    startingTime = int(data[startingIndex][0])
    for index in range(startingTime, int(data[-1][0]) + 1):
        timeArr.append(index)
        if index not in timeSet:
            RTCArr.insert(index - startingTime, None)
            PLArr.insert(index - startingTime, None)

    PLAvg = PLArr[-1]
    timeArr = averageArray(
        list(range(int(data[startingIndex][0] - secondsToPad), int(data[startingIndex][0]))) + timeArr, sliceSize, 1, 1)
    RTCArr = averageArray(([None] * secondsToPad + RTCArr), sliceSize, thresholdRTC, missingDataThreshold)
    PLArr = averageArray(([None] * secondsToPad + PLArr), sliceSize, 1, missingDataThreshold)
    timeArr = [datetime.fromtimestamp(t).strftime('%I:%M:%S%p') for t in timeArr]
    return timeArr, RTCArr, PLArr, PLAvg


def doPing(ping_dest, ping_size, ping_timeout, debug):
    """Pings a specific IP address once, and returns the results as a dictionary."""
    if int(ping_size) > 65500:
        sched.shutdown(wait=False)
        raise ValueError("Ping Size too large")
    ping_parser = pingparsing.PingParsing()
    transmitter = pingparsing.PingTransmitter()
    transmitter.destination = ping_dest
    transmitter.packet_size = ping_size
    transmitter.count = 1
    transmitter.timeout = str(ping_timeout) + 'ms'
    result = transmitter.ping()
    toReturn = ping_parser.parse(result).as_dict()
    logging.debug(toReturn)
    if toReturn["destination"] is None:
        sched.shutdown(wait=False)
        raise ValueError("Could not resolve host " + ping_dest)

    toReturn["timestamp"] = time.time()
    toReturn["rtt_avg"] = 0 if toReturn["packet_receive"] == 0 else toReturn["rtt_avg"]
    return toReturn


def recordPing(app: Flask):

    """Does a ping, and stores the results in a SQL table. Additionally, deletes records in SQL table that are older
    than 4 hours."""
    pingData = doPing(app.config['PING_DESTINATION'], int(app.config['PING_SIZE']), app.config['PING_TIMEOUT'],
                      app.config['DEBUG'])
    db = sqlite3.connect("db/pings.db")
    con = db.cursor()
    con.execute("""CREATE TABLE IF NOT EXISTS pings (
        timestamp REAL PRIMARY KEY,
        destination TEXT NOT NULL,
        packet_received INTEGER NOT NULL,
        RTT INTEGER NOT NULL)""")
    con.execute("""INSERT INTO pings VALUES (?, ?, ?, ?)"""
                , (pingData["timestamp"], pingData["destination"], pingData["packet_receive"], pingData["rtt_avg"]))
    con.execute("""DELETE FROM pings WHERE timestamp < ?""", (time.time() - 60 * 60 * 4,))
    db.commit()
    db.close()


def createTable():
    """Creates SQL Table if it doesn't exist"""
    db = sqlite3.connect("db/pings.db")
    con = db.cursor()
    con.execute("""CREATE TABLE IF NOT EXISTS pings (
    timestamp REAL PRIMARY KEY,
    destination TEXT NOT NULL,
    packet_received INTEGER NOT NULL,
    RTT INTEGER NOT NULL)""")
    db.commit()
    db.close()


@dataCollection.record
def beginDataCollection(state):
    Path("db/").mkdir(exist_ok=True)
    createTable()
    sched.add_job(recordPing, 'cron', second='*', args=[state.app])
    sched.start()

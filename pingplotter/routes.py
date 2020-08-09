import gzip
import json
import sqlite3
import time

from flask import Blueprint, render_template, make_response
from .dataCollection import calculateArray

from pingplotter import cache
from pingplotter.utils import *

routes = Blueprint('routes', __name__)



@routes.route("/latest.json")
@cache.cached(timeout=1)
def dataResponse():
    """Function returns a compressed JSON file with data sampled from array using the calculateArray function."""
    lastThreeHour = time.time() - 3 * 60 * 60
    lastHour = lastThreeHour + 2 * 60 * 60
    lastMinute = lastHour + 59 * 60
    db = sqlite3.connect("pings.db")
    cursor = db.cursor()
    cursor.execute("""SELECT * from pings WHERE timestamp > ? ORDER BY timestamp ASC""", (lastThreeHour,))
    data = cursor.fetchall()
    cursor.close()
    threeHourTimestamp, threeHourRTC, threeHourPL, threeHourPLAvg = calculateArray(data, lastThreeHour, 60, .5, .5)
    hourPingTimestamp, hourRTC, hourPL, hourPLAvg = calculateArray(data, lastHour, 60, .5, .5)
    minPingTimestamp, minRTC, minPL, minPLAvg = calculateArray(data, lastMinute, 1, .5, .5)
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


@routes.route("/")
def dashboard():
    return render_template('chart.html')

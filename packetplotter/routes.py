import gzip
import json
import sqlite3
import time

from flask import Blueprint, render_template, make_response, current_app
from .dataCollection import calculateArray

from packetplotter import cache
from packetplotter.utils import *

routes = Blueprint('routes', __name__)


@routes.route("/latest.json")
@cache.cached(timeout=1)
def dataResponse():
    """Function returns a compressed JSON file with data sampled from array using the calculateArray function."""
    lastThreeHour = time.time() - 3 * 60 * 60
    lastHour = lastThreeHour + 2 * 60 * 60
    lastMinute = lastHour + 59 * 60
    db = sqlite3.connect("db/pings.db")
    cursor = db.cursor()
    cursor.execute("""SELECT * from pings WHERE timestamp > ? ORDER BY timestamp ASC""", (lastThreeHour,))
    data = cursor.fetchall()
    cursor.close()
    threeHourTimestamp, threeHourRTT, threeHourPL, threeHourPLAvg = calculateArray(data, lastThreeHour, 60, .5, .5)
    hourPingTimestamp, hourRTT, hourPL, hourPLAvg = calculateArray(data, lastHour, 60, .5, .5)
    minPingTimestamp, minRTT, minPL, minPLAvg = calculateArray(data, lastMinute, 1, .5, .5)
    toReturn = {"min_RST_AVG": round(nonZeroMean(minRTT), 2),
                "threeHour_RST_AVG": round(nonZeroMean(threeHourRTT), 2),
                "hour_RST_AVG": round(nonZeroMean(hourRTT), 2),
                "min_PL_AVG": minPLAvg,
                "threeHour_PL_AVG": threeHourPLAvg,
                "hour_PL_AVG": hourPLAvg,
                "threeHourRTT": threeHourRTT,
                "threeHourPL": threeHourPL,
                "threeHourTimestamp": threeHourTimestamp,
                "hourRTT": hourRTT,
                "hourPL": hourPL,
                "hourTimestamp": hourPingTimestamp,
                "minuteRTT": minRTT,
                "minutePL": minPL,
                "minuteTimestamp": minPingTimestamp}
    compressedReturn = gzip.compress(json.dumps(toReturn).encode('utf8'))
    response = make_response(compressedReturn)
    response.headers['Content-length'] = len(compressedReturn)
    response.headers['Content-Encoding'] = 'gzip'
    return response


@routes.route("/")
def dashboard():
    return render_template('chart.html', PING_DESTINATION=current_app.config['PING_DESTINATION'])

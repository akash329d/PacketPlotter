# PacketPlotter
Generates charts for the Round Trip Time (RTT) and loss for packets over past minute, hour and three hours. Useful for tracking packet loss, and diagnosing network issues. Uses Python to gather ping data and parse data. SQLite is used to store ping data. Frontend uses ChartJS for graph creation. Flask/uWSGI for web server. Does 1 ping/sec.

Webpage:
![Screenshot](https://github.com/akash329d/PacketPlotter/blob/screenshots/screenshot.png?raw=true)

Can be configured from the config.ini file (or through environmental variables) 

Run With uWSGI (need to install uWSGI via PIP or other means):
```shell
uwsgi --http :8080 uwsgi.ini
```  
Or just run directly via Python and use Flask's built in Development Server:
```shell
python wsgi.py
```
Both options will use config from config.ini (prioritizes environmental variables)
## Docker Usage

Dockerhub: https://hub.docker.com/r/akash329d/packetplotter
Base Image: https://github.com/tiangolo/uwsgi-nginx-flask-docker  
(Uses Nginx/uWSGI)

### Example Docker Image Creation
```
docker create \
  --name=PacketPlotter \
  -e PING_DESTINATION=8.8.8.8 \
  -e PING_SIZE=32 \
  -e PING_TIMEOUT = 200 \
  -p 80:80 \
  -v /path/to/store/db:/app/db \
  akash329d/packetplotter
```

### Docker Parameters
Parameter|Description|Default Value
---|---|---
PING_DESTINATION|The server to ping.|8.8.8.8 (Google DNS Anycast IP)
PING_SIZE|Size of ping packet (in bytes)|32 Bytes
PING_TIMEOUT|Time before packet is considered "lost" |200ms
DEBUG|To run with debug mode (prints ping data)|False
-v /app/db|Used to map SQLite Database to host system. Not necessarily needed (will only be around 800KB max)| N/A


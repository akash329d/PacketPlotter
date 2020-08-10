FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine
ENV STATIC_PATH /app/packetplotter/static
copy packetplotter /app/packetplotter
copy uwsgi.ini /app
copy wsgi.py /app
copy config.py /app
copy requirements.txt /app
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt
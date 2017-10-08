FROM python:latest

ENV APP=barrenero-telegram

RUN apt-get update && \
    apt-get install -y \
        locales \
        locales-all
ENV LANG='es_ES.UTF-8' LANGUAGE='es_ES.UTF-8:es' LC_ALL='es_ES.UTF-8'

# Install build requirements
RUN apt-get update && \
    apt-get install -y \
        apt-transport-https \
        software-properties-common\
        git

# Create project dirs
RUN mkdir -p /srv/apps/$APP/logs
WORKDIR /srv/apps/$APP

RUN pip install --upgrade Cython

# Install pip requirements
COPY requirements.txt constraints.txt /srv/apps/$APP/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt

# Clean up
RUN apt-get clean && \
    apt-get purge --auto-remove -y \
        apt-transport-https \
        software-properties-common && \
    rm -rf $HOME/.cache/pip/* \
        /tmp/* \
        /etc/apt/sources.list.d/passenger.list \
        /var/tmp/* \
        /var/lib/apt/lists/* \
        /var/cache/apt/archives/*.deb \
        /var/cache/apt/archives/partial/*.deb \
        /var/cache/apt/*.bin

# Copy application
COPY . /srv/apps/$APP/

ENTRYPOINT ["./__main__.py"]

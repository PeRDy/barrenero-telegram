FROM python:alpine
LABEL maintainer="José Antonio Perdiguero López <perdy.hh@gmail.com>"

ENV APP=barrenero-telegram

RUN apk --no-cache add \
        build-base \
        linux-headers && \
    rm -rf /var/cache/apk/*

# Create project dirs
RUN mkdir -p /srv/apps/$APP/logs
WORKDIR /srv/apps/$APP

RUN python -m pip install --upgrade Cython

# Install pip requirements
COPY requirements.txt constraints.txt /srv/apps/$APP/
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt -c constraints.txt && \
    rm -rf $HOME/.cache/pip/*

# Copy application
COPY . /srv/apps/$APP/

ENTRYPOINT ["./__main__.py"]

FROM python:alpine
LABEL maintainer="José Antonio Perdiguero López <perdy.hh@gmail.com>"

ENV APP=barrenero-telegram

RUN apk --no-cache add \
        build-base \
        sqlite-dev \
        linux-headers && \
    rm -rf /var/cache/apk/*

# Create project dirs
RUN mkdir -p /srv/apps/$APP/logs
WORKDIR /srv/apps/$APP

# Install pip requirements
COPY Pipfile Pipfile.lock /srv/apps/$APP/
RUN python -m pip install --upgrade pip pipenv && \
    pipenv install --system --deploy --ignore-pipfile

# Copy application
COPY . /srv/apps/$APP/

ENTRYPOINT ["./__main__.py"]

FROM python:3.9.7-slim-buster

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1s
ENV PYTHONFAULTHANDLER 1
ENV DEBIAN_FRONTEND noninteractive

# TODO, load from somewhere else
ENV ARETHA_INTERFACE eth0


RUN apt-get update \
	&& apt-get -y install --no-install-recommends nmap \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /aretha
COPY . .

ENTRYPOINT ["./start.sh"]

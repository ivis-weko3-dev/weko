FROM python:3.14-slim

RUN pip3 install tavern
RUN pip3 install beautifulsoup4
RUN pip3 install psycopg2-binary
RUN pip3 install xmltodict

RUN apt-get -y update && apt-get -y install curl

WORKDIR /tavern

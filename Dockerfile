FROM            python:3.7.2-stretch

MAINTAINER      Sergiu Buhatel

WORKDIR         /app

COPY            . /app
COPY            pip.ini C:/ProgramData/pip/pip.ini
COPY            pip.ini /etc/pip.conf

VOLUME          ["/var/www"]

EXPOSE          7001

ENV             FLASK_APP=app.py

# Install FreeTDS and dependencies for PyODBC
ADD             odbcinst.ini /etc/odbcinst.ini
RUN             apt-get update
RUN             apt-get install gcc
RUN             apt-get install curl --force-yes --assume-yes
RUN             apt-get install gnupg --force-yes --assume-yes
RUN             apt-get install freetds-dev --force-yes --assume-yes
RUN             apt-get dist-upgrade --assume-yes --force-yes
RUN             apt-get install -y tdsodbc unixodbc-dev
RUN             apt install unixodbc-bin -y
RUN             apt-get install apt-transport-https
RUN             curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN             curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
RUN             apt-get clean -y
RUN             apt-get update
RUN             ACCEPT_EULA=Y apt-get install mssql-tools --force-yes --assume-yes

RUN             pip install -r requirements.txt
RUN             odbcinst -j

CMD             ["gunicorn", "--certfile=SSL/USPAVCOPSPD01_sha256/USPAVCOPSPD01.crt", "--keyfile=SSL/USPAVCOPSPD01_sha256/USPAVCOPSPD01.key", "--bind", "0.0.0.0:7001", "wsgi:app"]



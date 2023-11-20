FROM ubuntu:latest
RUN apt-get update && apt-get install -y \
cron \ 
python3 \
python3-pip
ADD config.json /usr/bin/config.json
ADD requirements.txt /usr/bin/requirements.txt
ADD source /usr/bin/source
ADD crontab /var/spool/cron/crontab

RUN pip3 install -r /usr/bin/requirements.txt
RUN chmod +x /usr/bin/source
RUN crontab /var/spool/cron/crontab

CMD ["cron", "-f"]

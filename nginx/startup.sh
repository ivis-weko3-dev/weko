#!/bin/bash

pm2="pm2 start /usr/local/ecosystem.config.js -s"
eval $pm2

tail -F /root/.pm2/logs/AMS-out.log >> /dev/stdout 2> >(grep -v "No such file or directory" >&2) &
tail -F /root/.pm2/logs/AMS-error.log >> /dev/stderr 2> >(grep -v "No such file or directory" >&2) &

supervisor="/usr/bin/supervisord -c /etc/supervisor/supervisord.conf"
eval $supervisor

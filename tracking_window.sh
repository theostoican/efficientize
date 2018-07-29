#!/bin/bash

LOGS_DIR='logs/'

while :
do
    DATE=`date +%Y-%m-%d`
    echo $DATE
    xdotool getactivewindow getwindowname >> $LOGS_DIR/$DATE
    sleep 1
done
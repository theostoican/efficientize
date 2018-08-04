#!/bin/bash

LOGS_DIR='logs/'

while :
do
    DATE=`date +%Y-%m-%d`
    echo $DATE
    curr_window=$(xdotool getactivewindow getwindowname)
    curr_time=$(date +"%T")
    echo "$curr_time,$curr_window," >> $LOGS_DIR/$DATE
    sleep 1
done
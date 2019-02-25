#!/bin/bash

BOTDIR="/home/redditbot/github/bots/userleansbot"
cd $BOTDIR

if ! ps -ef |grep -v grep | grep -q "python3 bot.py"; then
	ls -l 
    	/usr/bin/screen -dmS userleansbot python3 bot.py
else
	#echo "Bot running"
	exit 0
fi


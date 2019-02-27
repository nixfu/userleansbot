#!/bin/bash
export EDITOR=vi
export PIP_USER=yes
export PATH=/home/redditbot/.local/bin:$PATH
alias startlean="cd ~/github/bots/userleansbot;/usr/bin/screen -dmS userleansbot python3 bot.py"
alias leanlog="tail -f ~/github/bots/userleansbot/bot.log"
alias leanstatus="ps -ef|grep bot.py |grep -v grep"

BOTDIR="/home/redditbot/github/bots/userleansbot"
cd $BOTDIR


if ! ps -ef |grep -v grep | grep -q "python3 bot.py"; then
	#tmux new-session -d -s userleansbot 'python3 bot.py'
    	/usr/bin/screen -dmS userleansbot python3 bot.py
else
	#echo "Bot running" >> ${BOTDIR}/cron.log
	exit 0
fi


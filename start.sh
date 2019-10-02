#!/bin/bash
export EDITOR=vi
export PIP_USER=yes
#export PATH=/home/myredditbot/.local/bin:$PATH
alias startlean="cd ~/github/bots/userleansbot;/usr/bin/screen -dmS userleans python3 userleans.py"
alias leanlog="tail -f ~/github/bots/userleansbot/bot.log"
alias leanstatus="ps -ef|grep bot.py |grep -v grep"
export LC_ALL="en_US.UTF-8"

BOTDIR="/home/myredditbot/github/bots/userleansbot"
cd $BOTDIR

export TZ=EST5EDT

BOTPID=$(cat ${BOTDIR}/bot.pid)

if ! ps -ef |awk '{print $2}' |grep -q ${BOTPID}; then
	#tmux new-session -d -s userleansbot 'python3 bot.py'
    	/usr/bin/screen -dmS userleans python3 -u userleans.py
else
	echo "Bot running: pid=${BOTPID}"
	exit 0
fi


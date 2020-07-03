#!/bin/bash
export EDITOR=vi
export PIP_USER=yes
#export PATH=/home/myredditbot/.local/bin:$PATH
alias startlean="cd ~/github/bots/userleansbot;/usr/bin/screen -dmS userleans python3 userleans.py"
alias leanlog="tail -f ~/github/bots/userleansbot/bot.log"
alias leanstatus="ps -ef|grep bot.py |grep -v grep"
#export LC_ALL="en_US.UTF-8"

export BOTDIR="$HOME/github/bots/userleansbot"
cd $BOTDIR

export TZ=EST5EDT


if [ -f ${BOTDIR}/DONOTSTART ]; then
	exit 0
fi


if [ -f ${BOTDIR}/bot.pid ]; then
	BOTPID=$(cat ${BOTDIR}/bot.pid)
else
	echo "99999999999999999" > ${BOTDIR}/bot.pid
	BOTPID="999999999999999999"
fi

if ! ps -ef |awk '{print $2}' |grep -q ${BOTPID}; then
	#tmux new-session -d -s userleansbot 'python3 bot.py'
    	/usr/bin/screen -dmS userleans python3 -u userleans.py
else
	echo "Bot running: pid=${BOTPID}"
	exit 0
fi


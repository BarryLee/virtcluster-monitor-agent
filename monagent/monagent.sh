#! /bin/bash

DIR_PATH=$(cd "$(dirname "$0")"; pwd)
#echo $DIR_PATH
AGENT="agent"
#PYTHON="python2.6"

USAGE="Usage: "$0" start|stop|restart"

_error () {
    if [ "$#" = 0 ]
    then
        msg="$USAGE"
    else
        msg="$1"
    fi
    echo
    echo "$msg"
    echo
    exit 1
}

_isrunning () { ps ax|grep -i "$1"|grep -v grep; }

_killall () {
    ps ax|grep "$1"|grep -v grep|awk '{print $1}'|xargs kill
}

_getport () {
    cat "$DIR_PATH"/config/agent.conf | grep "port =" | awk '{print $3}'
}

_openport () {
    iptables -I INPUT -p tcp --dport "$1" -j ACCEPT
}

_start () {
    echo "starting ""$1"
    cmd=$DIR_PATH"/"$1
    if _isrunning "$cmd"
    then
        _error "$1"" is running"
    else
        $cmd start
    fi
}

_stop () {
    echo "stoping ""$1"
    "$DIR_PATH"/"$1" stop
}

if [ "$#" -ne 1 ]
then
    _error
fi

ACTION="$1"
PORT=`_getport`

if [ "$ACTION" = "start" ]
then
    _start $AGENT
    _openport $PORT
elif [ "$ACTION" = "stop" ]
then
    _stop $AGENT
elif [ "$ACTION" = "restart" ]
then
    _stop $AGENT
    sleep 2
    _start $AGENT
    _openport $PORT
else
    _error
fi

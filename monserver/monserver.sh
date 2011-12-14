#! /bin/bash

DIR_PATH=$(cd "$(dirname "$0")"; pwd)
#echo $DIR_PATH
SERVER="serverd"
EVENT_SERVER="event_serverd"
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

if [ "$ACTION" = "start" ]
then
    _start $EVENT_SERVER
    _start $SERVER
elif [ "$ACTION" = "stop" ]
then
    _stop $SERVER
    _stop $EVENT_SERVER
elif [ "$ACTION" = "restart" ]
then
    _stop $SERVER
    _stop $EVENT_SERVER
    sleep 2
    _start $EVENT_SERVER
    _start $SERVER
else
    _error
fi

#!/bin/bash

usage () {
    echo "$0 -d <agent_path> -p <remote_path>"
    echo 
}

CURDIR=$(cd "$(dirname "$0")"; pwd)
read VALUES < $CURDIR"/nodes"
Hosts=($VALUES)
RPrefix="/tmp"

while getopts "d:p:h" arg
do
    case $arg in 
        d)
            DPath=$OPTARG
            ;;
        p)
            RPrefix=$OPTARG
            ;;
        h)
            usage
            exit 0
            ;;
        ?)
            usage
            exit 1
            ;;
    esac
done

if [ ! -d $DPath ]
then
    echo "$DPath not exist"
    usage
    exit 1
fi

for h in "${Hosts[@]}"
do
	ssh $h "mkdir -p $RPrefix"
	scp -r $DPath $h:$RPrefix
	ssh $h "python $RPrefix/cranemonagent/monagent/agent restart"
done

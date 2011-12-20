#!/bin/bash

i=0

RRDDIR="/tmp/rrds"
META="metadata"

for d in `ls $RRDDIR`
do
    #echo "testing "$d
    if [ ! -e "$RRDDIR/$d/$META" ]
    then
        #echo $d" has no metadata"
        arr[i]="$d"
        (( i = i + 1 ))
    fi
done

echo ${arr[*]}

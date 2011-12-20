#!/bin/sh

for i in `python findunreachablevms.py |grep unreach|sed 's/^.*://'|xargs -d ,`; do ssh root@`sh vmip.sh $i` 'python /tmp/agent/mon_agent restart'; done;

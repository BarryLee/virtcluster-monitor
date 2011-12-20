#!/bin/sh

Hosts=(
	'cu01'
	'cu02'
	'cu03'
	'cu04'
	'cu05'
	'cu06'
	'cu07'
	'cu08'
	'cu09'
	'cu10'
      )

CMD='sh monitor/daemon/daemon.sh restart'

for h in "${Hosts[@]}"
do
	ssh $h $CMD
done

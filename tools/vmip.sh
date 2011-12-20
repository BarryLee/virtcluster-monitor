#!/bin/bash

ID=${1}

echo `onevm show $ID|grep IP_PUBLIC=|cut -d= -f2|cut -d, -f1`

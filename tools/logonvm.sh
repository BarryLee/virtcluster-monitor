#!/bin/bash

ID=${1}

ssh root@`cranevm show $ID|grep IP_PUBLIC=|cut -d= -f2|cut -d, -f1`

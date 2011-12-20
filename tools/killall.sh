#!/usr/bin/bash

ps ax|grep mon_center|awk '{print $1}'|xargs kill

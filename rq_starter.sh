#!/usr/bin/env bash
# $1 - worker name.

if [[ -z $1 ]] ; then
    echo "$0 worker_name"
    exit
fi

rq worker -c rq_config $1

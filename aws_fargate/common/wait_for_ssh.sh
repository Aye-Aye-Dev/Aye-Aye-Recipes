#!/bin/bash
# https://serverfault.com/questions/152795/linux-command-to-wait-for-a-ssh-server-to-be-up
HOST=$1
if [ -z "$1" ]
  then
    echo "Missing argument for host."
    exit 1 
fi

echo "polling to see that host is up and ready"
RESULT=1 # 0 upon success
TIMEOUT=20 # number of iterations (~160 seconds)
while :; do 
    echo "waiting for server ping ..."
    status=$(ssh -o BatchMode=yes -o ConnectTimeout=5 ${HOST} -o StrictHostKeyChecking=no echo ok 2>&1)
    RESULT=$?
    if [ $RESULT -eq 0 ]; then
        # this is not really expected unless a key lets you log in
        echo "connected ok"
        break
    fi
    if [ $RESULT -eq 255 ]; then
        # connection refused also gets you here
        if [[ $status == *"Permission denied"* ]] ; then
            # permission denied indicates the ssh link is okay
            echo "server response found"
            break
        fi
        if [[ $status == *"Too many authentication failures"* ]] ; then
            # permission denied indicates the ssh link is okay
            echo "server response found"
            break
        fi
    fi
    TIMEOUT=$((TIMEOUT-1))
    if [ $TIMEOUT -eq 0 ]; then
        echo "timed out"
        exit 1 
    fi
    sleep 3
done


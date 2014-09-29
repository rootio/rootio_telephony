#!/bin/zsh
screen -ls | grep Detached | cut -d. -f1 | awk '{print $1}' | xargs kill


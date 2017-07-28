#!/bin/ash
arecord -f cd -M test.wav &
sleep 1
aplay -M ./sound/500Hz_3s.wav
killall arecord
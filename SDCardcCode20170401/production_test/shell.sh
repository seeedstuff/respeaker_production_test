#!/bin/ash
#aplay 100_150Hz.wav &
arecord -f cd -t wav -M test.wav &
#aplay /Media/SD-P1/manufacture_program/sound/150Hz_single_left.wav
aplay /Media/SD-P1/manufacture_program/sound/150Hz_single_right.wav
# aplay /Media/SD-P1/manufacture_program/sound/400_150Hz_MIX.wav
# aplay /Media/SD-P1/manufacture_program/sound/1KHz.wav
#sleep 1
killall arecord
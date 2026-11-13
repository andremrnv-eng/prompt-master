#!/bin/bash
cd "$(dirname "$0")"
TOTAL=3336; P=3; STEP=$(( (TOTAL+P-1)/P ))
for k in $(seq 0 $((P-1))); do a=$((k*STEP)); b=$(( (k+1)*STEP )); [ $b -gt $TOTAL ] && b=$TOTAL; node render.js segment seg$k.mp4 $a $b > log$k.txt 2>&1 & done
wait
printf "file 'seg0.mp4'\nfile 'seg1.mp4'\nfile 'seg2.mp4'\n" > list.txt
ffmpeg -y -v error -f concat -safe 0 -i list.txt -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart apple_rejuvenation.mp4
echo RENDER_DONE

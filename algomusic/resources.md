# algomusic

Some useful software tools for inspecting music files:
```
go get github.com/hajimehoshi/go-mp3
go get github.com/hajimehoshi/oto
brew install ffmpeg
```

Get audo info from mp3:
```
afinfo input.mp3
```

View binary representation (9 columns wide) of mp3 file, starting at lines 47 and ending at 100:
```
xxd -b -c 9 input.mp3 | sed -n '47,100p'
```

Command for generating waveform video from mp3
```
ffmpeg -i input.mp3 -filter_complex "[0:a]showwaves=s=1920x1080:mode=line,format=yuv420p[v]" -map "[v]" -map 0:a -c:v libx264 -c:a copy output.mp4
```

## etc.

https://wavesurfer-js.org/


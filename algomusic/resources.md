# algomusic

Some useful software tools for inspecting music files

github.com/hajimehoshi/go-mp3
github.com/hajimehoshi/oto

Get audo info from mp3:
```
afinfo github.com/hajimehoshi/go-mp3/example/classic.mp3
```

View binary representation of mp3 file:
```
xxd -b -c 16 github.com/hajimehoshi/go-mp3/example/classic.mp3 | head
```

Command for generating waveform video from mp3
```
ffmpeg -i input.mp3 -filter_complex "[0:a]showwaves=s=1920x1080:mode=line,format=yuv420p[v]" -map "[v]" -map 0:a -c:v libx264 -c:a copy output.mp4
```

etc.

https://wavesurfer-js.org/


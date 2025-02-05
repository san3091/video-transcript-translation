# transalte and burn subtitles utility

this utility takes the mp4 video and the vtt transcript file in spanish prduced by zoom meeting recordings and translate it to english, then burns the subtitles onto a video

i use this utility in a clinical setting so it is very important that all the material be processed locally

TODO
* add a ui
* add support for other language pairs
  * there are already other language pairs available through transformers
* add flexible target video resolution (scale down to 720p or 576p for web storage)


## Usage

make sure `python` and `pip` are installed

the script makes system calls to `ffmpeg` for video processing so make sure `ffmpeg` is installed

with brew:

```
brew install ffmpeg
```

install dependencies

```
pip install -r requirements.txt
```

translate and burn subtitles

```
python translate_and_burn.py filename.mp4 captions.vtt
```

this will produce a file `filename_subtitled.mp4` in the same directory as the original `mp4` file

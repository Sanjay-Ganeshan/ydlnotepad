import argparse
import typing as T
import yt_dlp as youtube_dl
import os
import sys

from .paths import (
    DOWNLOADS,
)

def download_subtitles_and_video(video_links: T.List[str], av_spec: str = "v", lang: T.Optional[str] = "en"):
    postprocessors = []
    yt_params = {
        'writesubtitles': lang is not None,
        'subtitleslangs': [lang],
        'skip_download': False,
        'format': 'bestaudio' if "v" not in av_spec else 'bestvideo+bestaudio',
        'postprocessors': postprocessors,
        'outtmpl': os.path.join(DOWNLOADS, av_spec+'_%(title)s-%(id)s.%(ext)s'),
    }

    try:
        with youtube_dl.YoutubeDL(params=yt_params) as downloader:
            downloader.download(video_links)
    except Exception as exc:
        print(f"WARNING: download failed: {exc}", file=sys.stderr)    
    
def handle_file(file: str, default_to_audio_only: bool = False, lang: T.Optional[str] = "en") -> str:
    with open(file, "r") as f:
        lines = [l.strip() for l in f.read().splitlines() if "youtube.com" in l]
    spec_a = []
    spec_v = []
    spec_av = []
    for line in lines:
        spl = line.split()
        if len(spl) == 1:
            # Just a video, assume video only
            if default_to_audio_only:
                spec_a.append(spl[0])
            else:
                spec_v.append(spl[0])
        elif len(spl) == 2:
            assert spl[0] in ["av", "va", "a", "v"], f"Expected [download_spec] <link> - download spec should be [a][v] - maybe out of order? Got: {spl[0]}"
            want_audio = "a" in spl[0]
            want_video = "v" in spl[0]
            url = spl[1]
            if want_audio and want_video:
                spec_av.append(url)
            elif want_audio:
                spec_a.append(url)
            elif want_video:
                spec_v.append(url)
            else:
                raise ValueError(f"Expected one or both of av, got {spl[0]}")
        else:
            raise AssertionError(f"Expected [download_spec with one or both of a/v] <link> -- too long {spl}")
    
    download_subtitles_and_video(spec_a, av_spec= "a", lang=None)
    download_subtitles_and_video(spec_v, av_spec= "v", lang=lang)
    download_subtitles_and_video(spec_av, av_spec= "av", lang=lang)

def main():
    parser = argparse.ArgumentParser(description="Downloads a file containing youtube videos")
    parser.add_argument("file")
    parser.add_argument("--audio", action="store_true", default=False, help="audio only")
    args = parser.parse_args()
    filepath = os.path.abspath(args.file)
    handle_file(filepath, default_to_audio_only=False)



if __name__ == '__main__':
    main()


import os
import sys
import dataclasses
import subprocess
import typing as T
import time
from io import BytesIO
import argparse

from .paths import (
    DOWNLOADS,
    OUTPUT,
)

"""
Command looks like:

ffmpeg -i {in_webm} -f "webvtt" -i {in_subtitles} -c:v copy -c:a copy -c:s webvtt {out_mp4}
"""

@dataclasses.dataclass
class ConversionOperation:
    original_fname: str
    skip_overwrite: bool = dataclasses.field(default=True)
    remux_only: bool = dataclasses.field(default=True)

    def get_source_and_needed_conversions(self) -> T.Tuple[str, bool, bool]:
        """
        Returns (input video, should output video, should output audio)
        """
        video_path = os.path.abspath(os.path.join(DOWNLOADS, self.original_fname)).replace("/", "\\")
        spl = self.original_fname.split("_")
        prefix = spl[0]
        if os.path.isfile(video_path):
            return video_path, "v" in prefix, "a" in prefix
        else:
            raise FileNotFoundError(f"Could not find {self.original_fname}")
    
    def get_subtitle_track_and_type(self) -> T.Optional[T.Tuple[str, str]]:
        extensions = [
            (".en.vtt", "webvtt"),
            (".en.ssa", "ssa"),
            (".en.ass", "ass"),
            (".en.srt", "srt"),
        ]

        inp, _, _ = self.get_source_and_needed_conversions()
        
        base = os.path.splitext(inp)[0]
        for (ext, stype) in extensions:
            poss = base + ext
            if os.path.isfile(poss):
                return poss, stype
    
        return None
    
    def get_output_paths(self) -> T.Tuple[T.Optional[str], T.Optional[str]]:
        inp, video, audio = self.get_source_and_needed_conversions()
        noext_basename = os.path.splitext(os.path.basename(inp))[0]
        noext_basename = "_".join(noext_basename.split("_")[1:])
        video_basename = noext_basename + ".mp4"
        audio_basename = noext_basename + ".mp3"
        video_full = os.path.join(OUTPUT, video_basename).replace("/","\\")
        audio_full = os.path.join(OUTPUT, audio_basename).replace("/","\\")

        return (None if not video else video_full, None if not audio else audio_full)

    def already_exists(self) -> bool:
        vid, aud = self.get_output_paths()
        return (vid is None or os.path.isfile(vid)) and (aud is None or os.path.isfile(aud))

    def __post_init__(self) -> None:
        self.get_source_and_needed_conversions()
    
    def modify_ffmpeg_command(
        self, 
        input_options: T.List[str],
        output_options: T.List[str],
        next_input_index: int = 0, 
    ) -> int:
        src, _, _ = self.get_source_and_needed_conversions()
        out_vid, out_aud = self.get_output_paths()
        
        my_vid_ix = next_input_index
        next_input_index += 1
        input_options.extend(
            [
                "-i",
                src,
            ]
        )

        if out_vid is not None and (not self.skip_overwrite or not os.path.exists(out_vid)):
            assert os.path.exists(out_vid) == os.path.isfile(out_vid), f"Non-file: {out_vid}"
            output_options.extend(["-map", f"{my_vid_ix}"])
            sub_file_and_type = self.get_subtitle_track_and_type()
            if sub_file_and_type is not None:
                my_sub_ix = next_input_index
                next_input_index += 1
                sub_file, sub_type = sub_file_and_type
                input_options.extend(["-f", sub_type, "-i", sub_file])
                output_options.extend(["-map", f"{my_sub_ix}:s"])
                output_options.extend(["-c:s", "mov_text"])
            if self.remux_only:
                output_options.extend([f"-c:v", "copy"])
                output_options.extend([f"-c:a", "copy"])
            output_options.append(out_vid)
        
        if out_aud is not None and (not self.skip_overwrite or not os.path.exists(out_aud)):
            assert os.path.exists(out_aud) == os.path.isfile(out_aud), f"Non-file: {out_aud}"
            output_options.extend(["-map", f"{my_vid_ix}:a"])
            # Can't remux to mp3
            output_options.append(out_aud)
        
        return next_input_index

def clear_downloads() -> None:
    files = os.listdir(DOWNLOADS)
    for each_file in files:
        try:
            os.remove(os.path.join(DOWNLOADS, each_file))
        except Exception as err:
            print(f"Couldn't clean {each_file} -- {err}", file=sys.stderr)

def execute_conversions(ops: T.List[ConversionOperation]):
    # Executing them all jointly lets ffmpeg do any optimizations that it can
    program_options = [
        "ffmpeg",
        "-y",
    ]

    input_options = []
    output_options = []
    next_input_index = 0

    for each_op in ops:
        if not each_op.already_exists() or not each_op.skip_overwrite:
            next_input_index = each_op.modify_ffmpeg_command(
                input_options,
                output_options,
                next_input_index,
            )
    print(output_options)
    
    full_command = program_options + input_options + output_options
    #print("\n".join(full_command))
    if len(output_options) > 0:
        proc = subprocess.run(full_command, capture_output=True)
        if proc.returncode == 0:
            print("Success! Removing source files...")
            clear_downloads()
        else:
            print("Fail")
            print(proc.stderr.decode())



def get_conversion_operations(remux: bool = True) -> T.List[ConversionOperation]:
    good_ext = [".mkv", ".m4a", ".mp4", ".webm", ".mp3"]
    found = {fn for fn in os.listdir(DOWNLOADS) if os.path.splitext(fn)[1] in good_ext}
    return [ConversionOperation(fn, skip_overwrite=True, remux_only=remux) for fn in sorted(found)]

def main() -> None:
    parser = argparse.ArgumentParser(description="Converts everything in the downloads folder to mp3/mp4")
    parser.add_argument("--recode", action="store_true", help="actually re-encode streams")
    args = parser.parse_args()
    ops = get_conversion_operations(remux=not args.recode)
    execute_conversions(ops)

if __name__ == "__main__":
    main()


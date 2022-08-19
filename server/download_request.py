from dataclasses import dataclass

@dataclass
class DownloadRequest:
    video_id: str
    convert_video: bool
    convert_audio: bool
    subtitles: bool

    def av_spec(self) -> str:
        return (
            ("a" if self.convert_audio else "") + 
            ("v" if self.convert_video else "")
        )
    
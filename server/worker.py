import multiprocessing
from .batch_download import download_subtitles_and_video
from .batch_convert import get_conversion_operations, execute_conversions
from .download_request import DownloadRequest


def work(q: multiprocessing.Queue):
    print("Listening...")
    try:
        ops = get_conversion_operations(remux = True)
        execute_conversions(ops)
        print("Done converting!")
        while (item := q.get()) is not None:
            assert isinstance(item, DownloadRequest), f"Not DL: {item}"

            download_subtitles_and_video(
                [item.video_id], item.av_spec()
            )

            ops = get_conversion_operations(remux = True)
            execute_conversions(ops)
            print("Done converting!")


    except KeyboardInterrupt:
        pass
    print("Stopping!")

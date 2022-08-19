# Run with
# python -m flask --app "simple_server.py:app" run -p 8908 --host="0.0.0.0"

from flask import Flask, request, make_response
from urllib.parse import parse_qs, urlparse
import multiprocessing
from .download_request import DownloadRequest

class ServerState:
    download_queue: multiprocessing.Queue = None

app = Flask(__name__)

@app.route("/download", methods=["GET"])
def download():
    qs = parse_qs(urlparse(request.url).query)
    videoid = qs.get("v", [None])[0]
    use_audio = bool(int(qs.get("a", ["0"])[0]))
    use_video = bool(int(qs.get("d", ["0"])[0]))
    use_subs = bool(int(qs.get("s", ["0"])[0]))

    if request.method == "GET":
        js = {"vid": videoid}
        print(videoid, use_audio, use_video, use_subs)
        if ServerState.download_queue is not None:
            req = DownloadRequest(
                video_id=videoid,
                convert_video=use_video,
                convert_audio=use_audio,
                subtitles=use_subs,
            )
            ServerState.download_queue.put(req)
        response = make_response(js)
        response.status_code = 200
        return response
    else:
        response = make_response({"message": "Should be GET"})
        response.status_code = 405
        return response


def start_app(download_queue = None) -> None:
    ServerState.download_queue = download_queue
    app.run(
        host="0.0.0.0",
        port=8908,
        debug=False,
        load_dotenv=False,
    )

if __name__ == '__main__':
    start_app()
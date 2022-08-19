from multiprocessing import Process
import multiprocessing
multiprocessing.set_start_method("spawn")

def start_manager():
    q = multiprocessing.Queue()
    from .simple_server import start_app
    from .worker import work

    worker = multiprocessing.Process(
        target=work,
        args=(q,),
        daemon = True,
    )

    worker.start()

    start_app(q)
    worker.join()
    print("Done all!")

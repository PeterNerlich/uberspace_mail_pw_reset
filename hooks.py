import multiprocessing
import main

#workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
timeout = 30

def on_starting(server):
    main.startup()

def on_exit(server):
    main.shutdown()

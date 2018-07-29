import subprocess
import threading
import datetime
import os
from time import sleep

def worker():
    bashCommand = "./tracking_window.sh"

    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        
    # TODO: take into account error
    output, _ = process.communicate()
    


t = threading.Thread(target = worker)
t.start()

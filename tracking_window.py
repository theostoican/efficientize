import subprocess
import threading
import datetime
import os
import config
from time import sleep

def worker():
    bashCommand = "./tracking_window.sh"

    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        
    # TODO: take into account error
    output, _ = process.communicate()

def get_available_days():
    print(os.listdir(config.LOGS_DIR))
    


t = threading.Thread(target = worker)
t.start()

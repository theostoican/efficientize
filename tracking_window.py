import subprocess
import threading
import datetime
import os
import config
from time import sleep, strftime
from concurrent.futures import ThreadPoolExecutor



class Tracker:
    def __init__(self):
        executor = ThreadPoolExecutor(max_workers = config.NUM_THREADS)
       
        self.firstTime = None
        self.lastTime = None
        self.lastWindowName = None

        self.timelineFileName = datetime.datetime.today().strftime('%Y-%m-%d')
        self.timelineFileHandle = open(self.fileName, "a")
    
    def trackwindowName(self):
        trackCommand="xdotool getactivewindowName getwindowNamename"

        while True:
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

            windowName, _ = process.communicate()
            time = datetime.datetime.now().strftime('%H:%M:%S')

            # Send timeline processing activity task
            executor.submit(self.processTimeline, time, windowName)

            sleep(1)

    def processTimeline(self, time, windowName):
        if windowName == self.lastWindowName:
            self.lastTime = time
            record = time + "," + windowName + ","

            self.timelineFileHandle.write(record)
        else:
            self.lastWindowName = windowName
            self.firstTime = time



def worker():
    bashCommand = "./tracking_window.sh"

    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        
    # TODO: take into account error
    output, _ = process.communicate()

def get_available_days():
    return os.listdir(config.LOGS_DIR)
    


t = threading.Thread(target = worker)
t.start()

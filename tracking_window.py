import subprocess
import threading
import datetime
import os
import config
from time import sleep, strftime
from concurrent.futures import ThreadPoolExecutor


#TODO: Add timer for end of day to create another file
class Tracker:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers = config.NUM_THREADS)
       
        self.firstTime = None
        self.lastTime = None
        self.lastWindowName = None

        self.timelineFileName = config.LOGS_DIR + config.TIMELINE_DIR + datetime.datetime.today().strftime('%Y-%m-%d')                
        self.timelineFileHandle = open(self.timelineFileName, "a")

        # If this is a newly created file, print the header first
        if os.stat(self.timelineFileName).st_size == 0:
            self.timelineFileHandle.write("start,finish,window\n")
    
    def trackwindowName(self):
        trackCommand="xdotool getwindowfocus getwindowname"

        while True:
            process = subprocess.Popen(trackCommand.split(), stdout=subprocess.PIPE)

            windowName, _ = process.communicate()
            time = datetime.datetime.utcnow().strftime('%H:%M:%S')

            # Send timeline processing activity task
            self.executor.submit(self.processTimeline, time, windowName)

            sleep(1)

    def processTimeline(self, time, windowName):
        #print(windowName, self.lastWindowName)
        if windowName != self.lastWindowName:
            self.lastTime = time
            
            if self.lastWindowName:
                record = str(self.firstTime) + "," + str(self.lastTime) + "," + str(self.lastWindowName) + ",\n"
                self.timelineFileHandle.write(record)
                self.timelineFileHandle.flush()

            self.lastWindowName = windowName
            self.firstTime = time
    def getAvailableDays(self):
        return os.listdir(config.LOGS_DIR + config.TIMELINE_DIR)


def worker():
    bashCommand = "./tracking_window.sh"

    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        
    # TODO: take into account error
    output, _ = process.communicate()


    


#t = threading.Thread(target = worker)
#t.start()

#t = Tracker()
#t.trackwindowName()
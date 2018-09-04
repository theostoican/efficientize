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

        self.currHour = None
        #self.prepareFile()

    def prepareFile(self):
        self.currDay = datetime.datetime.today().strftime('%Y-%m-%d')
        # TODO: Might be an issue when we are at the end of the day
        self.currHour = datetime.datetime.now().strftime('%H')
        self.currDayDir = config.LOGS_DIR + config.TIMELINE_DIR + \
                self.currDay + '/'    
        self.timelineFileName = self.currDayDir + self.currHour

        if not os.path.exists(self.currDayDir):
            os.makedirs(self.currDayDir)             
        self.timelineFileHandle = open(self.timelineFileName, "a")

        # If this is a newly created file, print the header first
        if os.stat(self.timelineFileName).st_size == 0:
            self.timelineFileHandle.write("start,finish,window\n")
    
    def trackwindowName(self):
        trackCommand="xdotool getwindowfocus getwindowname"

        while True:
            process = subprocess.Popen(trackCommand.split(), stdout=subprocess.PIPE)

            windowName, _ = process.communicate()

            datetimeObject = datetime.datetime.now()
            time = datetimeObject.strftime('%H:%M:%S')
            hour = datetimeObject.strftime('%H')

            # Send timeline processing activity task
            self.executor.submit(self.processTimeline, time, hour, windowName)

            sleep(1)

    def processTimeline(self, time, hour, windowName):
        # Set up a new file for a new hour and flush the data for the
        # previous hour if the hour has changed
        if self.currHour is None or hour != self.currHour:
            if self.lastWindowName:
                # Flush the data
                lastSecondPrevHour = datetime.datetime.strptime(self.currHour + ":59:59", "%H:%M:%S").strftime("%H:%M:%S")
                print(lastSecondPrevHour)
                record = str(self.firstTime) + "," + str(lastSecondPrevHour) + "," + str(self.lastWindowName) + ",\n"
                self.timelineFileHandle.write(record)
                self.timelineFileHandle.flush()

                # Set new first time at the beginning of next hour
                self.firstTime = datetime.datetime.strptime(hour + ":00:00", "%H:%M:%S").strftime("%H:%M:%S")
            
            # Set up new file
            self.prepareFile()

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

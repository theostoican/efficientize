import subprocess
import threading
import queue
import datetime
import os
import config
from time import sleep, strftime
import csv

from pynput.keyboard import Key, Listener


class Tracker:
    def __init__(self):
        # Variables for app tracker
        self.firstTime = None
        self.lastTime = None
        self.lastWindowName = None

        self.currHour = None
        
        # Variables for keystroke tracker
        self.numKeystrokes = 0
        self.currWindowNumKeyStrokes = 0
        self.keyStrokesLock = threading.Lock()

        # Hashmaps for storing the time spent on apps and
        # the keystrokes recorded while in those apps
        self.timeMap = {}
        self.keystrokesMap = {}

        # Set how often we dump the top of the used apps (with
        # respect to keystrokes and to time) to 5 seconds
        self.intervalDump = 5

        # Start data processing thread
        # TODO: Modify variable name if we include other processing in the same
        # function besides timeline
        self.timelineQueue = queue.Queue()
        dataProcessor = threading.Thread(target = self.dispatchJobs)
        dataProcessor.daemon = True
        dataProcessor.start()

        # Start window tracker
        windowTracker = threading.Thread(target = self.trackWindowName)
        windowTracker.daemon = True
        windowTracker.start()

        # Start a listener thread corresponding to the keystroke tracker
        keystrokesTracker = threading.Thread(target = self.trackKeystrokes)
        keystrokesTracker.daemon = True
        keystrokesTracker.start()

    def trackKeystrokes(self):
        with Listener(on_press = self.onPress) as listener:
            listener.join()

    def prepareFile(self):
        # Variables used for keeping track of the timeline logs 
        self.currDay = datetime.datetime.today().strftime('%Y-%m-%d')
        # TODO: Might be an issue when we are at the end of the day
        self.currHour = datetime.datetime.now().strftime('%H')
        self.timelineDayDir = config.LOGS_DIR + config.TIMELINE_DIR + \
                self.currDay + '/'    
        timelineFileName = self.timelineDayDir + self.currHour

        if not os.path.exists(self.timelineDayDir):
            os.makedirs(self.timelineDayDir)

        self.timelineFileHandle = open(timelineFileName, "a")
        self.timelineFileCsvWriter = csv.writer(self.timelineFileHandle)

        # If this is a newly created file, print the header first
        if os.stat(timelineFileName).st_size == 0:
            self.timelineFileCsvWriter.writerow(["start", "finish", "window", "keystrokes"])

        # Variables used for keeping track of the time statistics logs
        self.timeDayDir = config.LOGS_DIR + config.TIME_DIR + \
                self.currDay + '/'

        # Variables used for keeping track of the keystrokes statistics logs  
        self.keystrokesDayDir = config.LOGS_DIR + config.KEYSTROKES_DIR + \
                self.currDay + '/'
  
    def onPress(self, _):
        self.keyStrokesLock.acquire()
        self.numKeystrokes += 1
        self.keyStrokesLock.release()

    def trackWindowName(self):

        trackCommand="xdotool getwindowfocus getwindowname"

        process = subprocess.Popen(trackCommand.split(), stdout=subprocess.PIPE) 

        windowName, _ = process.communicate()

        datetimeObject = datetime.datetime.now()
        time = datetimeObject.strftime('%H:%M:%S')
        hour = datetimeObject.strftime('%H')
        self.keyStrokesLock.acquire()
        numKeystrokes = self.numKeystrokes
        #print(numKeystrokes)
        self.numKeystrokes = 0
        self.keyStrokesLock.release()

        # Send timeline processing activity task
        self.timelineQueue.put((time, hour, windowName, numKeystrokes))
        threading.Timer(1.0, self.trackWindowName).start()
    
    def dispatchJobs(self):
        while True: 
            (time, hour, windowName, numKeystrokes) = self.timelineQueue.get()
            self.processTimeline(time, hour, windowName, numKeystrokes)
            self.timelineQueue.task_done()

    def processTimeline(self, time, hour, windowName, numKeystrokes):
        # Set up a new file for a new hour and flush the data for the
        # previous hour if the hour has changed or if this is the FIRST
        # information we record
        if self.currHour is None or hour != self.currHour:
            if self.lastWindowName:
                # Flush the data
                #TODO: Divide the numKeyStrokes if it is a new hour
                numKeystrokes += self.currWindowNumKeyStrokes
                print(time)
                print(self.firstTime)
                print((datetime.datetime.strptime(time, "%H:%M:%S") - \
                    datetime.datetime.strptime(self.firstTime, "%H:%M:%S")).total_seconds())

                # Divide keystrokes between the two intervals (before the end of the hour and
                # after it)
                totalDiff = (datetime.datetime.strptime(time, "%H:%M:%S") - \
                    datetime.datetime.strptime(self.firstTime, "%H:%M:%S")).total_seconds()
                roundHourDiff = (datetime.datetime.strptime(self.currHour + ":59:59", "%H:%M:%S") - \
                    datetime.datetime.strptime(self.firstTime, "%H:%M:%S")).total_seconds()

                firstPartKeystrokes = roundHourDiff / totalDiff * numKeystrokes
                
                self.currWindowNumKeyStrokes = numKeystrokes - firstPartKeystrokes
                lastSecondPrevHour = datetime.datetime.strptime(self.currHour + ":59:59", "%H:%M:%S").strftime("%H:%M:%S")
                print(lastSecondPrevHour)
                self.timelineFileCsvWriter.writerow([self.firstTime, lastSecondPrevHour, self.lastWindowName, firstPartKeystrokes / roundHourDiff])
                self.timelineFileHandle.flush()

                # Set new first time at the beginning of next hour
                self.firstTime = datetime.datetime.strptime(hour + ":00:00", "%H:%M:%S").strftime("%H:%M:%S")
            
            # Set up new file
            self.prepareFile()

        if windowName != self.lastWindowName:
            self.lastTime = time
            
            if self.lastWindowName:
                numKeystrokes += self.currWindowNumKeyStrokes
                print(self.lastWindowName)
                print(str(numKeystrokes))
                print('\n')
                self.currWindowNumKeyStrokes = 0
                totalTime = (datetime.datetime.strptime(self.lastTime, "%H:%M:%S") - \
                    datetime.datetime.strptime(self.firstTime, "%H:%M:%S")).total_seconds()

                self.timelineFileCsvWriter.writerow([self.firstTime,
                    self.lastTime, self.lastWindowName, numKeystrokes / totalTime])
                self.timelineFileHandle.flush()

            self.lastWindowName = windowName
            self.firstTime = time
        elif self.lastWindowName is not None:
            self.currWindowNumKeyStrokes += numKeystrokes


    def processKeyStrokes(self, windowName, numKeystrokes, dump):
        self.keystrokesMap[windowName] += numKeystrokes
        if dump % 5 == 0:
            pass

    def processTimeData(self, windowName, time, dump):
        self.timeMap[windowName] += time

    def getAvailableDays(self):
        availDates = os.listdir(config.LOGS_DIR + config.TIMELINE_DIR)
        
        availDates.sort()
        
        return availDates


def worker():
    bashCommand = "./tracking_window.sh"

    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
        
    # TODO: take into account error
    output, _ = process.communicate()


    


#t = threading.Thread(target = worker)
#t.start()

#t = Tracker()
#t.trackwindowName()

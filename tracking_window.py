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
        self.currTime = None
        
        # Variables for keystroke tracker
        self.numKeystrokes = 0
        self.currWindowNumKeyStrokes = 0
        self.keyStrokesLock = threading.Lock()

        # Hashmaps for storing the time spent on apps and
        # the keystrokes recorded while in those apps
        self.timeMap = {}
        self.keystrokesMap = {}

        # Variable used for knowing when we should dump statistics
        # to a new file, corresponding to another day
        self.currDay = None

        # Set how often we dump the top of the used apps (with
        # respect to keystrokes and to time) to 5 seconds
        self.intervalDump = 5
        self.dumpCounter = 0

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

    def createPathWithFile(self, pathToFile, fileName):
        if not os.path.exists(pathToFile):
            os.makedirs(pathToFile)

        fileHandle = open(fileName, "a")
        fileCsvWriter = csv.writer(fileHandle)

        # If this is a newly created file, print the header first
        if os.stat(fileName).st_size == 0:
            fileCsvWriter.writerow(["start", "finish", "window", "keystrokes"])

        return fileHandle, fileCsvWriter

    def prepareTimelineFile(self, day, hour):
        currDay = day
        self.currHour = hour

        # Variables used for keeping track of the timeline logs 
        timelineDayDir = config.LOGS_DIR + config.TIMELINE_DIR + \
                currDay + '/'    
        timelineFileName = timelineDayDir + self.currHour
        self.timelineFileHandle, self.timelineFileCsvWriter = \
                self.createPathWithFile(timelineDayDir, timelineFileName)
    
    def prepareStatisticsFile(self, time, day):
        self.currTime = time
        self.currDay = day

        # Variables used for keeping track of the time statistics logs
        timeDayDir = config.LOGS_DIR + config.TIME_DIR + '/'
        timeFileName = timeDayDir + self.currDay

        self.timeFileHandle, self.timeFileCsvWriter = \
            self.createPathWithFile(timeDayDir, timeFileName)

        # Variables used for keeping track of the keystrokes statistics logs  
        keystrokesDayDir = config.LOGS_DIR + config.KEYSTROKES_DIR + '/'
        keystrokesFileName = keystrokesDayDir + self.currDay

        self.keystrokesFileHandle, self.keystrokesCsvWriter = \
            self.createPathWithFile(keystrokesDayDir, keystrokesFileName)
  
    def onPress(self, _):
        self.keyStrokesLock.acquire()
        self.numKeystrokes += 1
        self.keyStrokesLock.release()

    def trackWindowName(self):

        trackCommand="xdotool getwindowfocus getwindowname"

        process = subprocess.Popen(trackCommand.split(), stdout=subprocess.PIPE) 

        windowName, _ = process.communicate()

        lastTimeRecord = datetime.datetime.now()
        day = lastTimeRecord.strftime('%Y-%m-%d')
        hour = lastTimeRecord.strftime('%H')
        self.keyStrokesLock.acquire()
        numKeystrokes = self.numKeystrokes
        #print(numKeystrokes)
        self.numKeystrokes = 0
        self.keyStrokesLock.release()

        # Send timeline processing activity task
        self.timelineQueue.put((lastTimeRecord, day, hour, windowName, numKeystrokes))
        threading.Timer(1.0, self.trackWindowName).start()
    
    def dispatchJobs(self):
        while True: 
            (time, day, hour, windowName, numKeystrokes) = self.timelineQueue.get()
            self.processTimeline(time, day, hour, windowName, numKeystrokes)
            self.timelineQueue.task_done()

    def processTimeline(self, time, day, hour, windowName, numKeystrokes):
        # Set up a new file for a new hour and flush the data for the
        # previous hour if the hour has changed or if this is the FIRST
        # information we record
        if self.currHour is None or hour != self.currHour:
            if self.lastWindowName:
                # Flush the data
                #TODO: Divide the numKeyStrokes if it is a new hour
                numKeystrokes += self.currWindowNumKeyStrokes

                # Divide keystrokes between the two intervals (before the end of the hour and
                # after it)
                totalDiff = (time - self.firstTime).total_seconds()

                lastTimePrevHour = time.replace(microsecond = 0, second = 0,
                    minute = 0)
                roundHourDiff = (lastTimePrevHour - self.firstTime).total_seconds()

                firstPartKeystrokes = roundHourDiff / totalDiff * numKeystrokes
                
                self.currWindowNumKeyStrokes = numKeystrokes - firstPartKeystrokes

                self.timelineFileCsvWriter.writerow(
                    [self.firstTime.strftime("%H:%M:%S"), 
                    lastTimePrevHour.strftime("%H:%M:%S"), self.lastWindowName,
                    firstPartKeystrokes / roundHourDiff])
                self.timelineFileHandle.flush()

                # Set new first time at the beginning of next hour
                self.firstTime = lastTimePrevHour

                # Make this variable 0, since both the hour and windowName
                # might change and we use this variable in the next if block
                numKeystrokes = 0
            
            # Set up new file
            self.prepareTimelineFile(day, hour)

        if windowName != self.lastWindowName:
            self.lastTime = time
            
            if self.lastWindowName:
                numKeystrokes += self.currWindowNumKeyStrokes
                self.currWindowNumKeyStrokes = 0
                totalTime = (self.lastTime - self.firstTime).total_seconds()

                self.timelineFileCsvWriter.writerow(
                    [self.firstTime.strftime("%H:%M:%S"),
                    self.lastTime.strftime("%H:%M:%S"), self.lastWindowName,
                    numKeystrokes / totalTime])
                self.timelineFileHandle.flush()

            self.lastWindowName = windowName
            self.firstTime = time
        elif self.lastWindowName is not None:
            self.currWindowNumKeyStrokes += numKeystrokes

    #def processStatistics(self, windowName, value, time, day, dump,):
    #    
    #    if day != self.currDay:
    #        if self.currDay is not None:
    #            totalTime = 
    #            
    #            
    #    dataMap[windowName] += value
    #    if dump % self.intervalDump == 0:
    #        for key in dataMap:
    #            csvWriter.writerow([key, dataMap[key]])
    #        fileHandle.flush()
    #        fileHandle.seek(0)
    #def processTimeStatistics(self, windowName, time, day):
    #    self.tim
    

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

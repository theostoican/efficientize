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
        self.currWindowNameNumKeyStrokes = 0
        self.keyStrokesLock = threading.Lock()

        # Variables used for storing the time spent on apps and
        # the keystrokes recorded while in those apps
        self.timeMap = {}
        self.keystrokesMap = {}
        self.currWindowName = None

        # Variable used for knowing when we should dump statistics
        # to a new file, corresponding to another day
        self.currDay = None
        self.currTime = None

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

    def createPathWithFile(self, pathToFile, fileName, header = None):
        if not os.path.exists(pathToFile):
            os.makedirs(pathToFile)

        fileHandle = open(fileName, "a")
        fileCsvWriter = csv.writer(fileHandle)

        # If this is a newly created file, print the header first
        if os.stat(fileName).st_size == 0 and header is not None:
            fileCsvWriter.writerow(header)

        return fileHandle, fileCsvWriter

    def prepareTimelineFile(self, day, hour):
        currDay = day
        timelineHeader = ["start", "finish", "window", "keystrokes"]

        # Variables used for keeping track of the timeline logs 
        timelineDayDir = config.LOGS_DIR + config.TIMELINE_DIR + \
                currDay + '/'    
        timelineFileName = timelineDayDir + self.currHour
        self.timelineFileHandle, self.timelineFileCsvWriter = \
                self.createPathWithFile(timelineDayDir, timelineFileName,
                timelineHeader)
        
        # Temp files
        self.timelineTmpFileName = config.LOGS_DIR + config.TMP_TIMELINE
        self.timelineTmpHandle, self.timelineTmpCsvWriter = \
            self.createPathWithFile(config.LOGS_DIR, self.timelineTmpFileName)
        
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
        dumpCnt = 0

        while True: 
            (time, day, hour, windowName, numKeystrokes) = self.timelineQueue.get()
            self.processTimeline(windowName, time, numKeystrokes, day, hour)
            self.processStatistics(windowName, time, numKeystrokes, day, dumpCnt)
            self.timelineQueue.task_done()

    def processTimeline(self, windowName, time, numKeystrokes, day, hour):
        # Set up a new file for a new hour and flush the data for the
        # previous hour if the hour has changed or if this is the FIRST
        # information we record
        if hour != self.currHour:
            if self.currHour is not None:
                # Flush the data
                #TODO: Divide the numKeyStrokes if it is a new hour
                numKeystrokes += self.currWindowNameNumKeyStrokes

                # Divide keystrokes between the two intervals (before the end of the hour and
                # after it)
                totalDiff = (time - self.firstTime).total_seconds()

                lastTimePrevHour = time.replace(microsecond = 0, second = 0,
                    minute = 0)
                roundHourDiff = (lastTimePrevHour - self.firstTime).total_seconds()

                firstPartKeystrokes = roundHourDiff / totalDiff * numKeystrokes
                
                self.currWindowNameNumKeyStrokes = numKeystrokes - firstPartKeystrokes

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
            
            # Set up new file for the new hour
            self.currHour = hour
            self.prepareTimelineFile(day, hour)

        if windowName != self.lastWindowName:
            self.lastTime = time
            
            if self.lastWindowName is not None:
                numKeystrokes += self.currWindowNameNumKeyStrokes
                self.currWindowNameNumKeyStrokes = 0
                totalTime = (self.lastTime - self.firstTime).total_seconds()

                self.timelineFileCsvWriter.writerow(
                    [self.firstTime.strftime("%H:%M:%S"),
                    self.lastTime.strftime("%H:%M:%S"), self.lastWindowName,
                    numKeystrokes / totalTime])
                self.timelineFileHandle.flush()

            self.lastWindowName = windowName
            self.firstTime = time
        else:
            self.currWindowNameNumKeyStrokes += numKeystrokes

    def processStatistics(self, windowName, time, numKeyStrokes, day, dumpCnt):
        statsHeader = ["window", "time", "keystrokes"]

        statsDir = config.LOGS_DIR + config.STATS_DIR

        # We have recorded at least once so far
        if self.currDay is not None:
            statsFileName = statsDir + self.currDay
            
        if day != self.currDay:
            # If this is not the first record (when self.currDay would be
            # none), proceed and dump the output for the previous day
            if self.currDay is not None:

                # Finish updating the time statistics map for the end of
                # the day
                lastTimePrevDay = time.replace(microsecond = 0, second = 0,
                    minute = 0, hour = 0)
                timeLeftBeforeEndOfDay = (lastTimePrevDay - \
                    self.currTime).total_seconds()
                self.timeMap[windowName] += timeLeftBeforeEndOfDay

                # Finish updating the keystrokes statistics map for the end
                # of the day
                totalTime = (time - self.currTime).total_seconds()
                keystrokesBeforeEndOfDay = timeLeftBeforeEndOfDay / totalTime * \
                                numKeyStrokes
                self.keystrokesMap[windowName] += keystrokesBeforeEndOfDay

                # Update the parameters for the case in which both the day
                # has ended and the app was switched with another one (dump
                # the data for the previous day but also dump the data
                # correspondent to the old app in the new day) 
                numKeyStrokes -= keystrokesBeforeEndOfDay
                self.currTime = lastTimePrevDay

                # Dump the data we have gathered so far until the end of the 
                # day
                self.dumpStatistics(statsFileName,
                    statsHeader)
            else:
                self.loadPreviousStats(statsDir + day)


            # Modify the file names with respect to the new day
            self.currDay = day
            statsFileName = statsDir + self.currDay

        # If we already have at least one record, update the maps
        # according to the new data
        if self.currWindowName:
            if self.currWindowName not in self.timeMap:
                self.timeMap[self.currWindowName] = 0
            self.timeMap[self.currWindowName] += (time - \
                self.currTime).total_seconds()
            
            if self.currWindowName not in self.keystrokesMap:
                self.keystrokesMap[self.currWindowName] = 0                                
            self.keystrokesMap[self.currWindowName] += numKeyStrokes

            # Dump at a specific interval into physical storage
            self.dumpStatistics(statsFileName,
                statsHeader)


        # Update the variables in order to be used for the next record
        self.currWindowName = windowName
        self.currTime = time

    def loadPreviousStats(self, fileName):
        # Try to integrate previous records for the same day,
        # if they exist
        try:
            with open(fileName, 'r') as statsFin:
                csvReader = csv.reader(statsFin, delimiter = ',')

                for row in csvReader:
                    window = row["window"]
                    time = row["time"]
                    keystrokes = row["keystrokes"]

                    if window not in self.timeMap:
                        self.timeMap[window] = time
                        self.keystrokesMap[window] = keystrokes
                    else:
                        self.timeMap[window] += time
                        self.keystrokesMap[window] += keystrokes
        except IOError:
            # If nothing was recorded so far in the current day, then do
            # nothing
            pass
    
    def dumpStatistics(self, fileName, header):
        # Create statistics file
        statisticsTmpFileName = config.LOGS_DIR + config.TMP_STATISTICS
        statisticsTmpHandle, statisticsTmpCsvWriter = \
            self.createPathWithFile(config.LOGS_DIR, statisticsTmpFileName)        
        
        # Write header
        statisticsTmpCsvWriter.writerow(header)

        # Write data into file
        for key in self.timeMap:
            statisticsTmpCsvWriter.writerow([key, self.timeMap[key], self.keystrokesMap[key]])

        # Flush on physical storage
        statisticsTmpHandle.flush()
        os.fsync(statisticsTmpHandle.fileno())
        statisticsTmpHandle.close()

        # Atomically rename the temp file with the "official"
        # file name
        os.rename(statisticsTmpFileName, fileName)

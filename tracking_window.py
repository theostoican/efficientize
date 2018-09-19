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

        # Variables used for storing all records necessary for
        # a timeline entry
        self.timelineBuffer = []

        # Variable used for knowing when we should dump statistics
        # to a new file, corresponding to another day
        self.currDay = None
        self.currTime = None

        # Set how often we dump the top of the used apps (with
        # respect to keystrokes and to time) to 5 seconds
        self.intervalDump = 5

        # Start data processing thread
        # function besides timeline
        self.taskQueue = queue.Queue()
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
        # Attempt to create path, if it does not already exist
        try:
            os.makedirs(pathToFile)
        except OSError:
            pass

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
        self.numKeystrokes = 0
        self.keyStrokesLock.release()

        # Send timeline processing activity task
        self.taskQueue.put((lastTimeRecord, day, hour, windowName, numKeystrokes))
        threading.Timer(1.0, self.trackWindowName).start()
    
    def dispatchJobs(self):
        dumpCnt = 0

        while True: 
            (time, day, hour, windowName, numKeystrokes) = self.taskQueue.get()
            self.processTimeline(windowName, time, numKeystrokes, day, hour, dumpCnt)
            self.processStatistics(windowName, time, numKeystrokes, day, dumpCnt)
            self.taskQueue.task_done()
            dumpCnt = (dumpCnt + 1) % self.intervalDump

    def processTimeline(self, windowName, time, numKeystrokes, day, hour, dumpCnt):
        timelineHeader = ["start", "finish", "window", "keystrokes"]

        if self.currHour is not None:
            timelineDayDir = config.LOGS_DIR + config.TIMELINE_DIR + \
                self.currDay + '/'    
            timelineFileName = timelineDayDir + self.currHour

        # Set up a new file for a new hour and flush the data for the
        # previous hour if the hour has changed or if this is the FIRST
        # information we record just set up a new file
        if hour != self.currHour:
            if self.currHour is not None:
                # Flush the data
                numKeystrokes += self.currWindowNameNumKeyStrokes

                # Divide keystrokes between the two intervals (before the end of the hour and
                # after it)
                totalDiff = (time - self.firstTime).total_seconds()

                lastTimePrevHour = time.replace(microsecond = 0, second = 0,
                    minute = 0)
                roundHourDiff = (lastTimePrevHour - self.firstTime).total_seconds()

                firstPartKeystrokes = int(roundHourDiff / totalDiff * numKeystrokes)
                
                self.currWindowNameNumKeyStrokes = numKeystrokes - firstPartKeystrokes

                self.timelineBuffer.append(
                    [self.firstTime.strftime("%H:%M:%S"), 
                    lastTimePrevHour.strftime("%H:%M:%S"), self.lastWindowName,
                    firstPartKeystrokes / roundHourDiff])
                
                self.dumpData('timeline', timelineDayDir, timelineFileName, timelineHeader)

                # Set new first time at the beginning of next hour
                self.firstTime = lastTimePrevHour

                # Empty the buffer, since we are switching to the next hour
                self.timelineBuffer = []

                # Make this variable 0, since both the hour and windowName
                # might change and we use this variable in the next if block
                numKeystrokes = 0
            else:
                currTimeFileName = config.LOGS_DIR + config.TIMELINE_DIR + \
                    day + '/' + hour
                self.loadPreviousTimelineData(currTimeFileName)
            
            # Set up new file for the new hour
            self.currHour = hour
            timelineDayDir = config.LOGS_DIR + config.TIMELINE_DIR + \
                day + '/'    
            timelineFileName = timelineDayDir + hour
            #self.prepareTimelineFile(day, hour)

        if windowName != self.lastWindowName:
            self.lastTime = time
            
            if self.lastWindowName is not None:
                numKeystrokes += self.currWindowNameNumKeyStrokes
                self.currWindowNameNumKeyStrokes = 0
                totalTime = (self.lastTime - self.firstTime).total_seconds()

                self.timelineBuffer.append(
                    [self.firstTime.strftime("%H:%M:%S"),
                    self.lastTime.strftime("%H:%M:%S"), self.lastWindowName,
                    numKeystrokes / totalTime])
                
                if dumpCnt % self.intervalDump == 0:
                    self.dumpData('timeline', timelineDayDir, timelineFileName, timelineHeader)

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
                keystrokesBeforeEndOfDay = int(timeLeftBeforeEndOfDay / totalTime * \
                                numKeyStrokes)
                self.keystrokesMap[windowName] += keystrokesBeforeEndOfDay

                # Update the parameters for the case in which both the day
                # has ended and the app was switched with another one (dump
                # the data for the previous day but also dump the data
                # correspondent to the old app in the new day) 
                numKeyStrokes -= keystrokesBeforeEndOfDay
                self.currTime = lastTimePrevDay

                # Dump the data we have gathered so far until the end of the 
                # day
                self.dumpData('stats', statsDir, statsFileName,
                    statsHeader)
                
                # Reset the maps that store information about statistics
                self.timeMap = {}
                self.keystrokesMap = {}
            else:
                self.loadPreviousStats(statsDir + day)

            # Modify the file names with respect to the new day
            self.currDay = day
            statsFileName = statsDir + day

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
            if dumpCnt % self.intervalDump == 0:
                self.dumpData('stats', statsDir, statsFileName,
                    statsHeader)


        # Update the variables in order to be used for the next record
        self.currWindowName = windowName
        self.currTime = time

    def loadPreviousTimelineData(self, fileName):
        # Try to integrate previous records for the same hour,
        # if they exist
        try:
            with open(fileName, 'r') as timelineFin:
                csvReader = csv.DictReader(timelineFin)

                for row in csvReader:
                    start = row["start"]
                    finish = row["finish"]                    
                    window = row["window"]
                    keystrokes = float(row["keystrokes"])

                    self.timelineBuffer.append([start, finish, window, keystrokes])
        except IOError:
            # If nothing was recorded so far in the current day, then do
            # nothing
            pass
    
    def loadPreviousStats(self, fileName):
        # Try to integrate previous records for the same day,
        # if they exist
        try:
            with open(fileName, 'r') as statsFin:
                csvReader = csv.DictReader(statsFin)

                for row in csvReader:
                    window = row["window"]
                    time = float(row["time"])
                    keystrokes = int(row["keystrokes"])

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

    # TODO
    # @type : can take two values : 
    #   -> 'stats' 
    #   -> 'timeline'
    def dumpData(self, type, dir, fileName, header):
        # Attempt to create path, if it does not already exist
        try:
            os.makedirs(dir)
        except OSError:
            pass

        # Create statistics file
        if type == 'stats':
            tmpFileName = config.LOGS_DIR + config.TMP_STATISTICS
        else:
            tmpFileName = config.LOGS_DIR + config.TMP_TIMELINE

        tmpHandle, tmpCsvWriter = \
            self.createPathWithFile(config.LOGS_DIR, tmpFileName)
        
        # Write header
        tmpCsvWriter.writerow(header)

        # Write data into file
        if type == 'stats':
            for key in self.timeMap:
                tmpCsvWriter.writerow([key, self.timeMap[key], self.keystrokesMap[key]])         
        else:
            for entry in self.timelineBuffer:
                tmpCsvWriter.writerow(entry)

        # Flush on physical storage
        tmpHandle.flush()
        os.fsync(tmpHandle.fileno())
        tmpHandle.close()
                
        # Atomically rename the temp file with the "official"
        # file name
        os.rename(tmpFileName, fileName)

    def dumpStatistics(self, statsDir, fileName, header):
        # Attempt to create path, if it does not already exist
        try:
            os.makedirs(statsDir)
        except OSError:
            pass

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

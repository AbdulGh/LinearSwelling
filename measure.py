from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *
import numpy as np
import random
import tools
import settings
import datetime

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class ExperimentWindow(Toplevel):
    def __init__(self, master, paramList):
        Toplevel.__init__(self, master)
        self.paramList = paramList
        self.initialReadings = [0 for _ in range(settings.numsensors)]
        self.currentReadings = None
        self.title("Swellometer measurement")
        self.resizable(False, False)

        self.initwindow()

    def initwindow(self):
        mainFrame = Frame(self)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True)

        leftFrame = Frame(mainFrame)
        leftFrame.pack(side=TOP, fill=BOTH, expand=True)

        inputFrame = Frame(leftFrame)
        inputFrame.grid(row=0, column=0, rowspan=3, columnspan=3)
        Label(inputFrame, text="Duration (m): ", width=15).grid(row=0, column=0, padx=5, pady=5)
        timeEntry = Entry(inputFrame)
        timeEntry.cname = "Duration"
        timeEntry.grid(row=0, column=1, padx=5)
        self.timeEntry = timeEntry

        rateL = Label(inputFrame, text="Readings/second: ", width=15)
        rateL.grid(row=2, column=0, padx=5, pady=5)
        rateEntry = Entry(inputFrame)
        rateEntry.insert(0, "2")
        rateEntry.cname = "Readings/second"
        rateEntry.grid(row=2, column=1, padx=5)
        self.rateEntry = rateEntry

        measurementFrame = Frame(leftFrame)
        measurementFrame.grid(row=1, column=0, rowspan=5, columnspan=3, pady=6)
        self.measurementFrame = measurementFrame

        btnFrame = Frame(measurementFrame)
        btnFrame.grid(row=0, column=0, rowspan=1, columnspan=3)
        stopBtn = Button(btnFrame, text="Stop", command=self.stopRecording)
        stopBtn.grid(row=0, column=0, padx=2)
        stopBtn.config(state=DISABLED)
        self.stopBtn = stopBtn
        startBtn = Button(btnFrame, text="Start", command=self.startRecording)
        startBtn.grid(row=0, column=1, padx=2)
        self.startBtn = startBtn

        graph = self.initGraphFrame(leftFrame)
        graph.grid(row=0, column=3, rowspan=15, columnspan=4)

        """
        checkboxFrame = Frame(leftFrame)
        self.renderSensorVars = []
        for i in range(settings.numsensors):
            var = IntVar()
            var.set(1)
            self.renderSensorVars.append(var)
            Checkbutton(checkboxFrame, text="Sensor " + str(i), command=self.updateGraph, variable=var).grid(row = i // 2, column = i % 2, padx=5, pady=5, sticky=N+E+S+W)
        checkboxFrame.grid(row=4, column=0, rowspan=3)
        """

        bottomBtnFrame = Frame(self)
        bottomBtnFrame.pack(side=BOTTOM, fill=X)
        Button(bottomBtnFrame, text="Done", command=self.fin).pack(side=RIGHT, padx=5, pady=5)
        self.exportBtn = Button(bottomBtnFrame, text="Export", command=self.exportReadings)
        self.exportBtn.pack(side=RIGHT, padx=(5,0))
        self.exportBtn.config(state=DISABLED)

    def exportReadings(self):
        if self.currentReadings is None:
            messagebox.showerror("No readings", "Please take some readings first")
            return

        f = filedialog.asksaveasfile(mode='w')
        if f is not None:
            delay = self.lastrate / 1000
            f.write("Calibration report - " + str(datetime.datetime.now()) + "\nRate - " + str(self.lastrate) + "\nTime(s) - Displacement(mm)\n")
            for s in range(len(self.currentReadings)):
                string = "\n***Sensor " + str(s) + "***\n"
                for i in range(len(self.currentReadings[s])):
                    string += str(round(delay * i, 4)) + " " + str(self.currentReadings[s][i]) + "\n"
                f.write(string)
            f.close()

    def stopRecording(self): #todo
        if self.animation is None:
            raise "check"

        self.animation.event_source.stop()

        self.stopBtn.config(state=DISABLED)
        self.startBtn.config(state=NORMAL)
        self.timeEntry.config(state=NORMAL)
        self.rateEntry.config(state=NORMAL)

        self.exportBtn.config(state=NORMAL)

    def fin(self):
        pass

    def updateGraph(self):
        pass

    def startRecording(self):
        if self.currentReadings is not None:
            result = messagebox.askquestion("Clear readings", "Discard current readings?", icon='warning')
            if result == "no":
                return

        time = tools.getFloatFromEntry(self.timeEntry, mini=0)
        rate = tools.getFloatFromEntry(self.rateEntry, mini=0.01)

        if (time is None or rate is None):
            return

        totalNo = time * rate * 60
        rate = self.lastrate = 1000/rate

        self.graph.set_xlim([0, time])

        self.stopBtn.config(state=NORMAL)
        self.startBtn.config(state=DISABLED)
        self.timeEntry.config(state=DISABLED)
        self.rateEntry.config(state=DISABLED)

        self.currentReadings = [[] for _ in range(settings.numsensors)]
        self.xs = np.linspace(0, time, totalNo)

        def takeSingleResult(_):
            if len(self.currentReadings) == totalNo:
                self.stopRecording()
                return
            for i in range(settings.numsensors):
                self.currentReadings[i].append(self.getCurrentDisplacement(i))
                plot = self.plots[i]
                plot.set_data(self.xs[:len(self.currentReadings[i])], self.currentReadings[i])

            return self.plots

        self.animation = matplotlib.animation.FuncAnimation(self.fig, takeSingleResult, interval=rate, blit=False)
        self.canvas.show()

    def getCurrentDisplacement(self, i):
        if i > len(self.initialReadings) or self.initialReadings[i] is None:
            raise "Displacement asked for before recording started"
        m,b = self.paramList[i] #todo
        return 1 + 2 * i + random.uniform(-0.3, 0.3) #m * (tools.getCurrentReading(i) - self.initialReadings[i]) + b

    def initGraphFrame(self, fr):
        f = plt.figure(figsize=(8, 5), dpi=100)
        self.fig = f
        a = f.add_subplot(111)
        a.set_xlabel("Time (m)")
        a.set_ylabel("Displacement (mm)")
        self.maxY = 10
        a.set_xlim([0,180])
        a.set_ylim([0,self.maxY])
        self.plots = []
        for i in range(settings.numsensors):
            l, = a.plot([])
            self.plots.append(l)
        self.graph = a

        wrapper = Frame(fr)
        canvas = FigureCanvasTkAgg(f, wrapper)
        self.canvas = canvas
        canvas.show()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        return wrapper

    """
    def currentReadingUpdate(self, label):
        update = int(1000 / tools.getFloatFromEntry(self.rateEntry, mini=0))
        def readingUpdate():
            i = tools.getCurrentReading()
            label.config(text="Current displacement(mm): " + str(i))
            self.readoutAfterID = label.after(update, readingUpdate)
        if self.readoutAfterID is not None:
            label.after_cancel(self.readoutAfterID)
        readingUpdate()"""

if __name__ == '__main__':
    root = Tk()
    measure = ExperimentWindow(root, [[1,1],[2,2],[3,4], [2,2]])
    root.wait_window(measure)
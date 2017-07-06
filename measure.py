from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *
import numpy as np
import random
import tools
import settings
import datetime
from time import *

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
        self.exported = False
        self.title("Swellometer measurement")
        self.resizable(False, False)

        self.style = Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.initwindow()

    def initwindow(self):
        mainFrame = Frame(self)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True)

        topFrame = Frame(mainFrame)
        topFrame.pack(side=TOP, fill=BOTH, expand=True)

        inputFrame = Frame(topFrame)
        inputFrame.pack(side=LEFT, padx=8, pady=8)
        Label(inputFrame, text="Duration (m): ", width=15).grid(row=0, column=0, padx=5, pady=5)
        timeEntry = Entry(inputFrame)
        timeEntry.cname = "Duration"
        timeEntry.grid(row=0, column=1, padx=5)
        self.timeEntry = timeEntry

        rateL = Label(inputFrame, text="Readings/minute: ", width=15)
        rateL.grid(row=2, column=0, padx=5, pady=5)
        rateEntry = Entry(inputFrame)
        rateEntry.insert(0, "2")
        rateEntry.cname = "Readings/minute"
        rateEntry.grid(row=2, column=1, padx=5)
        self.rateEntry = rateEntry

        btnFrame = Frame(topFrame)
        btnFrame.pack(side=RIGHT, padx=8, pady=8)
        stopBtn = Button(btnFrame, text="Stop", command=self.stopRecording)
        stopBtn.grid(row=0, column=0, padx=2)
        stopBtn.config(state=DISABLED)
        self.stopBtn = stopBtn
        startBtn = Button(btnFrame, text="Start", command=self.startRecording)
        startBtn.grid(row=0, column=1, padx=2)
        self.startBtn = startBtn

        graph = self.initGraphFrame(mainFrame)
        graph.pack(side=RIGHT, fill=BOTH, padx=8, pady=8)

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
        Button(bottomBtnFrame, text="Done", command=self.fin).pack(side=RIGHT, padx=8, pady=8)
        self.exportBtn = Button(bottomBtnFrame, text="Export", command=self.exportReadings)
        self.exportBtn.pack(side=RIGHT, padx=(5,0))
        self.exportBtn.config(state=DISABLED)

    def exportReadings(self):
        if self.currentReadings is None:
            messagebox.showerror("No readings", "Please take some readings first")
            return

        f = filedialog.asksaveasfile(mode='w')
        if f is not None:
            f.write("Calibration report - " + str(datetime.datetime.now()) + "\nRate - " + str(self.lastrate) + "\nTime(s) - Displacement(mm) - Voltage(mV)\n")
            for s in range(len(self.currentReadings)):
                string = "\n***Sensor " + str(s) + "***\n"
                string += "Recieved calibration line: y = " + str(self.paramList[s][0]) + " x + " + str(self.paramList[s][1]) + "\n"
                for i in range(len(self.currentReadings[s])):
                    string += str(round(self.actualTimes[s][i] * 10, 4)) + " " + str(self.currentReadings[s][i]) + " " + str(self.currentVoltages[s][i]) + "\n"
                f.write(string)
            f.close()
            self.exported = True

    def stopRecording(self):
        if self.animation is None:
            raise "check"

        self.animation.event_source.stop()

        self.stopBtn.config(state=DISABLED)
        self.startBtn.config(state=NORMAL)
        self.timeEntry.config(state=NORMAL)
        self.rateEntry.config(state=NORMAL)

        self.exportBtn.config(state=NORMAL)

    def fin(self):
        if self.currentReadings is not None and not self.exported:
            result = messagebox.askquestion("Results not exported", "Save results first?", icon='warning')
            if result == "yes":
                self.exportReadings()
        self.destroy()

    def startRecording(self):
        if self.currentReadings is not None and not self.exported:
            result = messagebox.askquestion("Results not exported", "Discard current readings?", icon='warning')
            if result == "no":
                return

        self.exported = False

        time = tools.getFloatFromEntry(self.timeEntry, mini=0)
        rate = tools.getFloatFromEntry(self.rateEntry, mini=0.01, maxi=120)

        if (time is None or rate is None):
            return

        totalNo = int(time * rate)
        rate = self.lastrate = 60000/rate

        self.graph.set_xlim([0, time])

        self.stopBtn.config(state=NORMAL)
        self.startBtn.config(state=DISABLED)
        self.timeEntry.config(state=DISABLED)
        self.rateEntry.config(state=DISABLED)

        self.currentReadings = [[] for _ in range(settings.numsensors)]
        self.currentVoltages = [[] for _ in range(settings.numsensors)]
        self.actualTimes = [[] for _ in range(settings.numsensors)]
        self.xs = np.linspace(0, time, totalNo)

        def takeSingleResult(_): #takes <=3.5ms starting empty w/ random input
            if len(self.currentReadings[0]) >= totalNo:
                self.stopRecording()
                return
            for i in range(settings.numsensors):
                d, v = self.getCurrentDisplacement(i)
                self.currentReadings[i].append(d)
                self.currentVoltages[i].append(v)
                self.actualTimes[i].append(clock() - self.lastStartTime)
                plot = self.plots[i]
                plot.set_data(self.xs[:len(self.currentReadings[i])], self.currentReadings[i])
            return self.plots

        self.lastStartTime = clock()
        self.animation = matplotlib.animation.FuncAnimation(self.fig, takeSingleResult, interval=rate, blit=False)
        self.canvas.show()

    def getCurrentDisplacement(self, i):
        if i > len(self.initialReadings) or self.initialReadings[i] is None:
            raise "Displacement asked for before recording started"
        m,b = self.paramList[i] #todo
        return [1 + 2 * i + random.uniform(-0.3, 0.3), random.randint(0, 10)] #m * tools.getCurrentReading(i) - self.initialReadings[i]) + b

    def initGraphFrame(self, fr):
        if "dark_background" in plt.style.available:
            plt.style.use("dark_background")
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

        wrapper = Frame(fr, relief=SUNKEN, borderwidth=1)
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
    measure = ExperimentWindow(None, [[1,1],[2,2],[3,4],[2,2]])
    root.wait_window(measure)
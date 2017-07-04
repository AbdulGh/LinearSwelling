from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *
import scipy.stats

import tools

import matplotlib
import matplotlib.animation
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class ExperimentWindow(Frame):
    def __init__(self, master, m, b):
        Frame.__init__(self, master)
        self.master = master
        self.m = m
        self.b = b
        self.initialReading = None
        """self.master.minsize(1100,550)
        self.master.geometry("1100x550")"""
        self.master.resizable(False, False)

        self.xs = []
        self.ys = []

        self.initwindow()

    def initwindow(self):
        self.master.title("Swellometer measurement")
        self.pack(fill=BOTH, expand=True, padx=6, pady=6)

        mainFrame = Frame(self)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True)

        leftFrame = Frame(mainFrame)
        leftFrame.pack(side=TOP, fill=BOTH, expand=True)

        inputFrame = Frame(leftFrame)
        inputFrame.grid(row=0, column=0, rowspan=3, columnspan=3)
        secondsL = Label(inputFrame, text="Duration (s): ", width=20)
        secondsL.grid(row=0, column=0, padx=5, pady=5)
        secondsEntry = Entry(inputFrame)
        secondsEntry.cname = "Duration"
        secondsEntry.grid(row=0, column=1, padx=5)
        self.secondsEntry = secondsEntry

        rateL = Label(inputFrame, text="Readings/second: ", width=20)
        rateL.grid(row=2, column=0, padx=5, pady=5)
        rateEntry = Entry(inputFrame)
        rateEntry.insert(0, "2")
        rateEntry.cname = "Readings/second"
        rateEntry.grid(row=2, column=1, padx=5)
        self.rateEntry = rateEntry

        measurementFrame = Frame(leftFrame)
        measurementFrame.grid(row=2, column=0, rowspan=5, columnspan=3, pady=6)
        self.measurementFrame = measurementFrame

        btnFrame = Frame(measurementFrame)
        btnFrame.grid(row=0, column=0, rowspan=1, columnspan=3)
        cancelBtn = Button(btnFrame, text="Cancel", command=self.cancelRecording)
        cancelBtn.grid(row=0, column=0, padx=2)
        cancelBtn.config(state=DISABLED)
        self.cancelBtn = cancelBtn
        startBtn = Button(btnFrame, text="Start", command=self.startRecording)
        startBtn.grid(row=0, column=1, padx=2)
        self.startBtn = startBtn

        curReading = Label(measurementFrame)
        self.currentReadingUpdate(curReading)
        curReading.grid(row=1, column=0, columnspan=2)

        graph = self.initGraphFrame(leftFrame)
        graph.grid(row=0, column=3, rowspan=15, columnspan=4)

        bottomBtnFrame = Frame(self)
        bottomBtnFrame.pack(side=BOTTOM, fill=X)
        exitBtn = Button(bottomBtnFrame, text="Done", command=self.fin)
        exitBtn.pack(side=RIGHT, padx=5, pady=5)

    def startRecording():
        seconds = getFloatFromEntry(self.secondsEntry, mini=0, forceInt=True)
        rate = getFloatFromEntry(self.rateEntry, mini=0)

        if (distance is None or rate is None):
            return

        self.initialReading = getCurrentReading()
        totalNo = seconds * rate
        seconds = int(seconds)
        rate = int(1000/rate)

        self.cancelBtn.config(state=NORMAL)
        self.startBtn.config(state=DISABLED)

        def takeSingleResult():
            if len(currentReadings) == totalNo:
                finalise()
                self.stopReadings()
                return

            i = self.getCurrentDisplacement()
            currentReadings.append(i)
            self.measurementAfterID = self.measurementFrame.after(rate, takeSingleResult)

    def currentReadingUpdate(self, label):
        update = int(1000 / getFloatFromEntry(self.rateEntry, mini=0))
        def readingUpdate():
            i = self.getCurrentReading()
            label.config(text="Current displacement(mm): " + str(i))
            self.readoutAfterID = label.after(update, readingUpdate)
        if self.readoutAfterID is not None:
            label.after_cancel(self.readoutAfterID)
        readingUpdate()

    def getCurrentDisplacement(self):
        if self.initialRecording is None:
            raise "Displacement asked for before recording started"
        return m * (getCurrentReading() - self.initialRecording) + b

    def initGraphFrame(self, fr):
        f = Figure(figsize=(8, 5), dpi=100)
        a = f.add_subplot(111)
        a.set_xlabel("Time (s)")
        a.set_ylabel("Displacement (mm)")
        self.maxX = 300
        self.maxY = 10
        a.set_xlim([0,self.maxX])
        a.set_ylim([0,self.maxY])
        a.scatter(self.xs, self.ys)
        self.graph = a

        wrapper = Frame(fr)
        canvas = FigureCanvasTkAgg(f, wrapper)
        canvas.show()
        self.canvas = canvas

        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        return wrapper
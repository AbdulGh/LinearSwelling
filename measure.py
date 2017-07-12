from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter.ttk import *
import tools
import settings
import time

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ExperimentWindow(Toplevel):
    def __init__(self, master, sensorsettings):
        Toplevel.__init__(self, master)
        self.paramList = []
        self.sensors = []
        for triple in sensorsettings:
            try:
                if len(triple) != 3:
                    raise ValueError
                self.sensors.append(int(triple[0]))
                self.paramList.append(triple[1:])
            except:
                raise ValueError("Bad input")
        self.sensorNames = ["Sensor " + str(i+1) for i in self.sensors]

        self.currentPercentageSwelling = None
        self.exported = False
        self.animation = None
        self.title("Swellometer measurement")
        self.resizable(False, False)

        self.connection = tools.DAQInput()

        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Rename test", command=self.getName)
        filemenu.add_command(label="Export results", command=self.exportReadings)
        filemenu.add_command(label="Exit", command=self.fin)
        menubar.add_cascade(label="File", menu=filemenu)
        settingsMenu = Menu(menubar, tearoff=0)
        settingsMenu.add_command(label="Name sensors", command=self.nameSensors)
        menubar.add_cascade(label="Settings", menu=settingsMenu)
        self.config(menu=menubar)

        self.protocol('WM_DELETE_WINDOW', self.fin)

        """
        self.style = Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        """
        self.name = time.ctime()
        self.initwindow()
        self.getName()

    def getName(self):
        while True:
            self.name = simpledialog.askstring("Name", "Test name:", initialvalue=self.name)
            if self.name is None:
                self.name = time.ctime()

            if self.name == "":
                messagebox.showerror("Name", "Name cannot be empty.")
                self.name = None
            else:
                break

    def nameSensors(self):
        t = Toplevel(self)

        t.geometry("+%d+%d" % (self.winfo_rootx() + 80, self.winfo_rooty() + 80))

        t.title("Sensors")
        fr = Frame(t)
        fr.pack(fill=BOTH, expand=True, padx=8, pady=8)
        entries = []
        labels = []
        for i in range(len(self.sensors)):
            spare = Frame(fr)
            spare.pack(side=TOP, fill=X, pady=(0,4))
            e = Entry(spare)
            e.insert(0, self.sensorNames[i])
            entries.append(e)
            e.pack(side=LEFT)
            l = Label(spare)
            l.pack(side=LEFT)
            labels.append(l)

        def updateLabels():
            for i in range(len(self.sensors)):
                labels[i].config(text=": " + str(self.connection.read(i)) + " mV")
            t.after(500, updateLabels)

        updateLabels()

        def updateNames():
            values = [entry.get() for entry in entries]
            #check sensors have unique names
            #could be done w/ a map or sorting but we have like 4 sensors
            for i in range(len(values)):
                for j in range(i+1, len(values)):
                    if values[i] == values[j]:
                        messagebox.showerror("Error", "Sensor names must have distinct names.")
                        return

            self.sensorNames = values
            self.graph.legend(labels = self.sensorNames)
            self.canvas.show()
            t.destroy()

        Button(fr, text="Save", command=updateNames).pack(side=RIGHT, padx=(8,0))
        Button(fr, text="Cancel", command=t.destroy).pack(side=RIGHT)
        t.resizable(False, False)

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
        #Button(btnFrame, text="Name sensors...", command=self.nameSensors).grid(row=0, column=0, padx=2)
        stopBtn = Button(btnFrame, text="Stop", command=self.stopRecording)
        stopBtn.grid(row=0, column=1, padx=2)
        stopBtn.config(state=DISABLED)
        self.stopBtn = stopBtn
        startBtn = Button(btnFrame, text="Start", command=self.startRecording)
        startBtn.grid(row=0, column=2, padx=2)
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
        #self.exportBtn = Button(bottomBtnFrame, text="Export", command=self.exportReadings)
        #self.exportBtn.pack(side=RIGHT, padx=(5,0))
        #self.exportBtn.config(state=DISABLED)

        progressFrame = Frame(bottomBtnFrame)
        self.progressLabel = Label(progressFrame, text="Waiting...", width=10)
        self.progressLabel.pack(side=LEFT)
        self.progressBar = Progressbar(progressFrame, orient=HORIZONTAL, length=200, mode='determinate')
        self.progressBar.pack(side=LEFT, fill=X, expand=True, padx=(8,0))
        progressFrame.pack(side=LEFT, fill=X, expand=True, padx=8, pady=8)

    def exportReadings(self):
        if self.currentPercentageSwelling is None:
            messagebox.showerror("No readings", "Please take some readings first.", parent=self)
            return

        f = filedialog.asksaveasfile(mode='w', parent=self)
        if f is not None:
            f.write(self.name + "\n" + time.ctime() + "\n" + str(time.time()) + "\nRate " + str(1000/self.lastrate) + "\nTime(m) - Displacement(%) - Voltage(mV)\n")
            for s in range(len(self.currentPercentageSwelling)):
                string = "\n*** " + self.sensorNames[s] + " ***\n"
                string += "Recieved calibration line: y = " + str(self.paramList[s][0]) + " x + " + str(self.paramList[s][1]) + "\n"
                string += "Initial reading: " + str(self.initialReadings[s][0]) + " " + str(self.initialReadings[s][1]) + "\n"
                for i in range(len(self.currentPercentageSwelling[s])):
                    string += str(self.actualTimes[s][i]) + " " + str(self.currentPercentageSwelling[s][i]) + " " + str(self.currentVoltages[s][i]) + "\n"
                f.write(string)
            f.close()
            self.exported = True

    def stopRecording(self):
        if self.animation is None:
            return

        self.animation.event_source.stop()
        self.animation = None

        self.stopBtn.config(state=DISABLED)
        self.startBtn.config(state=NORMAL)
        self.timeEntry.config(state=NORMAL)
        self.rateEntry.config(state=NORMAL)
        #self.exportBtn.config(state=NORMAL)

        self.progressLabel.config(text="Done.")
        self.progressBar["value"] = 0

    def fin(self):
        if self.animation: #still recording
            result = messagebox.askquestion("Test in progress", "Stop testing?", icon='warning', parent=self)
            if result == "no":
                return
            self.stopRecording()

        if self.currentPercentageSwelling is not None and not self.exported:
            result = messagebox.askquestion("Results not exported", "Do you want to save the current results?",
                                                icon='warning', parent=self, type=messagebox.YESNOCANCEL)
            print(result)
            if result == "cancel":
                return
            if result == "yes":
                self.exportReadings()
        self.destroy()

    def startRecording(self):
        if self.currentPercentageSwelling is not None and not self.exported:
            result = messagebox.askquestion("Results not exported", "Discard current readings?", icon='warning', parent=self)
            if result == "no":
                return

        self.exported = False

        t = tools.getFloatFromEntry(self.timeEntry, mini=0)
        rate = tools.getFloatFromEntry(self.rateEntry, mini=0.01, maxi=120)

        if (time is None or rate is None):
            return

        totalNo = int(t * rate) + 1
        rate = self.lastrate = 60000/rate
        self.progressBar.config(maximum=totalNo)

        self.graph.set_xlim([0, t])

        self.stopBtn.config(state=NORMAL)
        self.startBtn.config(state=DISABLED)
        self.timeEntry.config(state=DISABLED)
        self.rateEntry.config(state=DISABLED)

        self.initialReadings = [self.getCurrentDisplacement(i) for i in range(len(self.sensors))]
        multipliers = [50 for i in range(len(self.sensors))] #[100/self.initialReadings(i)[0] for i in range(len(self.sensors))] #pre-compute conversion constant into percentage swell
        self.currentPercentageSwelling = [[] for _ in range(len(self.sensors))]
        self.currentVoltages = [[] for _ in range(len(self.sensors))]
        self.actualTimes = [[] for _ in range(len(self.sensors))]

        def takeSingleResult(_): #takes <= 3.5ms starting empty w/ random input
            prog = len(self.currentPercentageSwelling[0])
            if prog >= totalNo:
                self.stopRecording()
                return
            self.progressBar["value"] = prog
            self.progressLabel.config(text = str(round(prog/totalNo * 100, 3)) + "%")
            for i in range(len(self.sensors)):
                d, v = self.getCurrentDisplacement(i)
                percentage = d * multipliers[i]
                if (percentage > self.maxY):
                    self.maxY = percentage + 10
                    self.graph.set_ylim([100, self.maxY])
                self.currentPercentageSwelling[i].append(d * multipliers[i])
                self.currentVoltages[i].append(v)
                self.actualTimes[i].append((time.time() - self.lastStartTime) / 60)
                plot = self.plots[i]
                plot.set_data(self.actualTimes[i], self.currentPercentageSwelling[i])
            return self.plots

        self.lastStartTime = time.time()
        self.animation = matplotlib.animation.FuncAnimation(self.fig, takeSingleResult, interval=rate, blit=False)
        self.canvas.show()

    def getCurrentDisplacement(self, i): #todo rename
        m,b = self.paramList[i]
        v = self.connection.read(i)
        return  [m * v + b, v]

    def initGraphFrame(self, fr):
        f = plt.figure(figsize=(8, 5), dpi=100)
        self.fig = f
        a = f.add_subplot(111)
        a.set_xlabel("Time (m)")
        a.set_ylabel("Relative swell (%)")
        self.maxY = 300
        a.set_xlim([0,180])
        a.set_ylim([100,self.maxY])
        self.plots = []
        for i in range(len(self.sensors)):
            l, = a.plot([], label=self.sensorNames[i])
            self.plots.append(l)
        h, l = a.get_legend_handles_labels()
        a.legend(h, l)
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
            label.config(text="Current displacement(%): " + str(i))
            self.readoutAfterID = label.after(update, readingUpdate)
        if self.readoutAfterID is not None:
            label.after_cancel(self.readoutAfterID)
        readingUpdate()"""

if __name__ == '__main__':
    root = Tk()
    root.withdraw()
    measure = ExperimentWindow(root, [[1,1],[2,2],[3,4],[2,2]])
    root.wait_window(measure)

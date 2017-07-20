from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *
import tools
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
        for sensor in sensorsettings:
            try:
                self.sensors.append(sensor[0])
                self.paramList.append(sensor[1:])
            except Exception:
                raise ValueError("Bad input")
        self.sensorNames = ["Sensor " + str(i+1) for i in self.sensors]
        self.initialThicknesses = [2 for _ in range(len(self.sensors))]
        self.currentPercentageSwelling = None #percentage swelling of ongoing run
        self.exported = False
        self.animation = None #matplotlib graph animation
        self.title("Swellometer measurement")
        self.resizable(False, False)
        self.connection = tools.DAQInput()
        self.outputWindow = None

        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Export results", command=self.exportReadings)
        filemenu.add_command(label="Clear results", command=self.clearResults)
        filemenu.add_command(label="Exit", command=self.fin)
        menubar.add_cascade(label="File", menu=filemenu)
        settingsMenu = Menu(menubar, tearoff=0)
        settingsMenu.add_command(label="Set up sensors", command=self.setupSensors)
        settingsMenu.add_command(label="Test settings", command=self.setupTest)
        menubar.add_cascade(label="Settings", menu=settingsMenu)
        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Sensor outputs", command=self.launchOutputWindow)
        menubar.add_cascade(label="View", menu=viewmenu)
        
        self.config(menu=menubar)
        self.protocol('WM_DELETE_WINDOW', self.fin)
        self.name = time.ctime()
        self.initwindow()
        self.notes = ""
        self.setupTest()
        self.setupSensors()
        self.lift() #the shell keeps jumping in front for whatever reason
        self.attributes("-topmost", 1)
        self.attributes("-topmost", 0)

    def clearResults(self):
        if messagebox.askyesno("Clear Results", "Are you sure you want to reset the test?", parent=self):
            self.stopRecording()
            #self.sensorNames = ["Sensor " + str(i + 1) for i in self.sensors]
            #self.initialThicknesses = [2 for _ in range(len(self.sensors))]
            self.currentPercentageSwelling = None
            self.exported = False
            self.animation = None
            self.graph.clear()
            self.graph.set_xlabel("Time (m)")
            self.graph.set_ylabel("Relative swell (%)")
            self.graph.set_xlim([0, 180])
            self.graph.set_ylim([95, self.maxY])

            self.plots = []
            for i in range(len(self.sensors)):
                l, = self.graph.plot([], label=self.sensorNames[i])
                self.plots.append(l)
            h, l = self.graph.get_legend_handles_labels()
            self.graph.legend(h, l)

            self.canvas.show()

    def setupTest(self):
        t = Toplevel(self)
        t.geometry("+%d+%d" % (self.winfo_rootx() + 80, self.winfo_rooty() + 80))
        t.title("Test settings")
        fr = Frame(t)
        fr.pack(fill=BOTH, expand=True, padx=8, pady=8)
        nameFrame = Frame(fr)
        nameFrame.pack(side=TOP, fill=X, expand=True)
        Label(nameFrame, text="Test name: ").pack(side=LEFT)
        nameEntry = Entry(nameFrame)
        nameEntry.insert(0, self.name)
        nameEntry.pack(side=LEFT, padx=(4,0), fill=X, expand=True)

        notesFrame = Frame(fr)
        notesFrame.pack(side=TOP, fill=BOTH, expand=True, pady=(4,0))
        Label(notesFrame, text="Test notes:", anchor=W, justify=LEFT).pack(side=TOP, anchor=W)
        notes = Text(notesFrame, height=15, width=50)
        notes.insert(END, self.notes)
        notes.pack(side=TOP, fill=BOTH, expand=True, pady=4)

        def setTestSettings():
            name = nameEntry.get()
            if name == "":
                messagebox.showerror("Error", "Test name cannot be empty.", parent=self)
                return
            self.name = name
            self.notes = notes.get("1.0", END)
            t.destroy()

        Button(fr, text="Done", command=setTestSettings).pack(side=RIGHT)
        t.resizable(False, False)

        t.grab_set()
        self.wait_window(t)

    def setupSensors(self):
        t = Toplevel(self)
        t.geometry("+%d+%d" % (self.winfo_rootx() + 80, self.winfo_rooty() + 80))
        t.title("Sensors")
        fr = Frame(t)
        fr.pack(fill=BOTH, expand=True, padx=8, pady=8)
        nameentries = []
        thicknessentries = []
        Label(fr, text="Sensor Name").grid(row=0, column=0, padx=(0,4))
        Label(fr, text="Initial thickness(mm)").grid(row=0, column=1, padx=(4,0))
        stat = NORMAL if self.currentPercentageSwelling is None else DISABLED #disallow changes to initial thicknesses if the test has started - we calculate relative swell
        for i in range(len(self.sensors)):
            e = Entry(fr)
            e.insert(0, self.sensorNames[i])
            nameentries.append(e)
            e.grid(row=i+1, column=0, pady=2, padx=(0,4))
            th = Entry(fr)
            th.insert(0, str(self.initialThicknesses[i]))
            th.config(state = stat)
            thicknessentries.append(th)
            th.grid(row=i+1, column=1, pady=2, padx=(4,0))

        def updateSettings():
            values = [entry.get() for entry in nameentries]
            #check sensors have unique names
            #could be done asymptotically faster w/ a map or sorting but we have like 4 sensors
            for i in range(len(values)):
                for j in range(i+1, len(values)):
                    if values[i] == values[j]:
                        messagebox.showerror("Error", "Sensor names must have distinct names.", parent=self)
                        return
                    
            self.initialThicknesses = []
            for i in range(len(self.sensors)):
                thickness = tools.getFloatFromEntry(self, thicknessentries[i], "Thickness " + str(i+1), mini=0.1)
                if thickness is None:
                    return
                self.initialThicknesses.append(thickness)

            self.sensorNames = values
            self.graph.legend(labels = self.sensorNames)
            self.canvas.show()
            t.destroy()

        Button(fr, text="Save", command=updateSettings).grid(row=len(self.sensors) + 1, column=1, sticky=E,  padx=(8,0), pady=(4,0))
        t.resizable(False, False)

        t.grab_set()
        self.wait_window(t)

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
        rateEntry.insert(0, "30")
        rateEntry.cname = "Readings/minute"
        rateEntry.grid(row=2, column=1, padx=5)
        self.rateEntry = rateEntry

        btnFrame = Frame(topFrame)
        btnFrame.pack(side=RIGHT, padx=8, pady=8)
        stopBtn = Button(btnFrame, text="Stop", command=self.stopRecording)
        stopBtn.grid(row=0, column=1, padx=2)
        stopBtn.config(state=DISABLED)
        self.stopBtn = stopBtn
        startBtn = Button(btnFrame, text="Start", command=self.startRecording)
        startBtn.grid(row=0, column=2, padx=2)
        self.startBtn = startBtn

        graph = self.initGraphFrame(mainFrame)
        graph.pack(side=RIGHT, fill=BOTH, padx=8, pady=8)

        bottomBtnFrame = Frame(self)
        bottomBtnFrame.pack(side=BOTTOM, fill=X)
        Button(bottomBtnFrame, text="Done", command=self.fin).pack(side=RIGHT, padx=8, pady=8)
        
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

        f = filedialog.asksaveasfile(mode='w', parent=self, defaultextension=".data", filetypes=[("Data File", "*.data")])
        if f is not None:
            f.write(self.name + "\n" + time.ctime() + "\n" + str(time.time()) + "\nRate " + str(1000/self.lastrate) + "\nNotes:\n")
            notes = self.notes.translate(str.maketrans({"\\": r"\\"}))
            f.write(notes + "\n\\\n")
            f.write("Time(m) - Displacement(%) - Voltage(mV)\n")
            for s in range(len(self.currentPercentageSwelling)):
                string = "\n*** " + self.sensorNames[s] + " ***\n"
                string += "Initial thickness (mm): " + str(self.initialThicknesses[s]) + "\n"
                string += "Initial displacement (mm): " + str(self.initialReadings[s]) + "\n"
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

        self.progressLabel.config(text="Done.")
        self.progressBar["value"] = 0

    def startRecording(self):
        if self.currentPercentageSwelling is not None and not self.exported:
            result = messagebox.askquestion("Results not exported", "Discard current readings?", icon='warning', parent=self)
            if result == "no":
                return

        self.exported = False

        t = tools.getFloatFromEntry(self, self.timeEntry, "Duration", mini=0)
        rate = tools.getFloatFromEntry(self, self.rateEntry, "Readings/minute", mini=0.01, maxi=120)

        if time is None or rate is None:
            return

        totalNo = int(t * rate) + 1
        rate = self.lastrate = 60000/rate

        self.graph.set_xlim([0, t])

        self.stopBtn.config(state=NORMAL)
        self.startBtn.config(state=DISABLED)
        self.timeEntry.config(state=DISABLED)
        self.rateEntry.config(state=DISABLED)

        self.progressBar.config(maximum=10)
        self.progressLabel.config(text="Starting...")
        self.update()

        #get average initial displacements
        readings = [[] for _ in range(len(self.sensors))]
        for i in range(10):
            self.progressBar["value"] = i
            self.update()
            for s in range(len(self.sensors)):
                readings[s].append(self.getCurrentDisplacementVoltage(s)[0])
            time.sleep(0.2)
        self.initialReadings = [sum(j)/len(j) for j in readings]
        
        multipliers = [100/self.initialThicknesses[i] for i in range(len(self.sensors))] #pre-compute conversion constant into percentage swelling
        self.currentPercentageSwelling = [[] for _ in range(len(self.sensors))]
        self.currentVoltages = [[] for _ in range(len(self.sensors))]
        self.actualTimes = [[] for _ in range(len(self.sensors))]
        self.progressBar.config(maximum=totalNo)

        def takeSingleResult(_):
            prog = len(self.currentPercentageSwelling[0])
            if prog >= totalNo:
                self.stopRecording()
                return
            self.progressBar["value"] = prog
            self.progressLabel.config(text = str(round(prog/totalNo * 100, 2)) + "%")
            for i in range(len(self.sensors)):
                d, v = self.getCurrentDisplacementVoltage(i)
                d = self.initialReadings[i] - d
                percentage = 100 + d * multipliers[i]
                if (percentage > self.maxY):
                    self.maxY = percentage + 10
                    self.graph.set_ylim([100, self.maxY])
                self.currentPercentageSwelling[i].append(percentage)
                self.currentVoltages[i].append(v)
                self.actualTimes[i].append((time.time() - self.lastStartTime) / 60)
                plot = self.plots[i]
                plot.set_data(self.actualTimes[i], self.currentPercentageSwelling[i])
            return self.plots

        self.lastStartTime = time.time()
        self.animation = matplotlib.animation.FuncAnimation(self.fig, takeSingleResult, interval=rate, blit=True)
        self.canvas.show()

    def launchOutputWindow(self):
        if self.outputWindow is None or not self.outputWindow.winfo_exists(): #closed or was never opened
            self.outputWindow = tools.DAQRawOutputDialog(self, self.connection)
            self.outputWindow.mainloop()
        else:
            self.outputWindow.lift()

    def getCurrentDisplacementVoltage(self, i):
        points = self.paramList[i]
        v = self.connection.read(self.sensors[i])
        return  [piecewiseLinearInterpolate(points, v), v]

    def initGraphFrame(self, fr):
        f = plt.figure(figsize=(8, 5), dpi=100)
        self.fig = f
        a = f.add_subplot(111)
        a.set_xlabel("Time (m)")
        a.set_ylabel("Relative swell (%)")
        self.maxY = 300
        a.set_xlim([0,180])
        a.set_ylim([95,self.maxY])
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

    def fin(self):
        if self.animation: #still recording
            result = messagebox.askquestion("Test in progress", "Stop testing?", icon='warning', parent=self)
            if result == "no":
                return
            self.stopRecording()

        if self.currentPercentageSwelling is not None and not self.exported:
            result = messagebox.askquestion("Results not exported", "Do you want to save the current results?",
                                                icon='warning', parent=self, type=messagebox.YESNOCANCEL)
            if result == "cancel":
                return
            if result == "yes":
                self.exportReadings()

        if self.outputWindow is not None and self.outputWindow.winfo_exists():
            self.outputWindow.destroy()
        self.destroy()

#xs must be sorted in ascending order!
def piecewiseLinearInterpolate(points, xval):    
    if len(points) < 2:
        raise ValueError("Need at least two points!")
    #check if we're past the left, extrapolate using first two points if so
    if xval < points[0][0]:
        x1, y1 = points[0]
        x2, y2 = points[1]
        m = (y2 - y1) / (x2 - x1)
        return y1 - m * (x2 - xval)
    for i in range(len(points) - 1):
        if xval > points[i+1][0]:
            continue
        else:
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            deltax = xval - points[i][0]
            return y1 + (y2 - y1) * (xval - x1)/(x2-x1)
    #if we get here we're past the last point - just extrapolate the last gradient
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    m = (y2 - y1) / (x2 - x1)
    return y2 + m * (xval - x2)

if __name__ == '__main__':
    print("Run main.py")

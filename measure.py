import os
import time
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import *

import matplotlib

import tools

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ExperimentWindow(Toplevel):
    def __init__(self, master, sensorsettings, daqconnection):
        print("expwindow init start")
        Toplevel.__init__(self, master)
        self.paramList = []
        self.sensors = []
        for sensor in sensorsettings:
            try:
                if len(sensor) != 3:
                    raise ValueError("Bad input")
                self.sensors.append(int(sensor[0]))
                self.paramList.append(sensor[1:])
            except Exception as e:
                raise ValueError("Bad input")

        self.running = False
        self.sensorNames = ["Sensor " + str(i+1) for i in self.sensors]
        self.todisplay = [IntVar(value=1) for _ in self.sensors]
        self.initialThicknesses = [2 for _ in range(len(self.sensors))]
        self.currentPercentageSwelling = None #percentage swelling of ongoing run (becomes a list of lists, one for each sensor)
        self.currentVoltages = None 
        self.actualTimes = None
        self.lastSaveTime = None #last time we dumped into a file
        self.nextUnsavedIndex = None #where we have saved to
        self.animation = None #matplotlib graph animation
        self.title("Swellometer measurement")
        self.resizable(False, False)
        self.connection = daqconnection
        self.outputWindow = None

        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Export results", command=self.exportUnsavedReadings)
        filemenu.add_command(label="Restart test", command=self.restart)
        filemenu.add_command(label="Exit", command=self.fin)
        menubar.add_cascade(label="File", menu=filemenu)
        settingsMenu = Menu(menubar, tearoff=0)
        settingsMenu.add_command(label="Set up sensors", command=self.setupSensors)
        settingsMenu.add_command(label="Test settings", command=self.setupTest)
        menubar.add_cascade(label="Settings", menu=settingsMenu)
        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Sensor outputs", command=self.launchOutputWindow)
        viewmenu.add_command(label="Displayed results", command=self.toShowDialog)
        menubar.add_cascade(label="View", menu=viewmenu)
        self.menubar = menubar
        
        self.config(menu=menubar)
        self.protocol('WM_DELETE_WINDOW', self.fin)
        self.name = time.ctime()
        self.filename = ""
        self.initwindow()
        self.notes = ""
        self.setupTest()
        self.setupSensors()
        self.lift() #the shell keeps jumping in front for whatever reason
        self.attributes("-topmost", 1)
        self.attributes("-topmost", 0)
        print("expwindow init end")

    def restart(self):
        if messagebox.askyesno("Clear Results", "Are you sure you want to reset the test?", parent=self):
            self.stopRecording()
            self.currentPercentageSwelling = None
            self.currentVoltages = None
            self.actualTimes = None
            self.lastSaveTime = None
            self.nextUnsavedIndex = None
            self.animation = None
            self.running = False
            self.todisplay = [IntVar(value=1) for _ in self.sensors]
            self.filename = ""
            self.graph.clear()
            self.graph.set_xlabel("Time (m)")
            self.graph.set_ylabel("Relative swell (%)")
            self.maxX = 1
            self.maxY = 150
            self.graph.set_xlim([0, self.maxX])
            self.graph.set_ylim([0, self.maxY])

            self.plots = []
            for i in range(len(self.sensors)):
                l, = self.graph.plot([], label=self.sensorNames[i])
                self.plots.append(l)
            h, l = self.graph.get_legend_handles_labels()
            self.graph.legend(h, l)

            self.canvas.show()

            self.menubar.entryconfig("Settings", state="normal")

            self.setupTest()
            self.setupSensors()

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
        Label(nameFrame, text="Filename: ").pack(side=LEFT, padx=(4,0))

        def selectFileName():
            filename = filedialog.asksaveasfilename(parent=t, defaultextension=".data",
                                         filetypes=[("Data File", "*.data")])
            if self.filename != "" and filename != self.filename:
                os.remove(self.filename)
            self.filename = filename

        Button(nameFrame, text='Choose...', command=selectFileName).pack(side=LEFT)

        notesFrame = Frame(fr)
        notesFrame.pack(side=TOP, fill=BOTH, expand=True, pady=(4,0))
        Label(notesFrame, text="Test notes:", anchor=W, justify=LEFT).pack(side=TOP, anchor=W)
        notes = Text(notesFrame, height=15, width=50)
        notes.insert(END, self.notes)
        notes.pack(side=TOP, fill=BOTH, expand=True, pady=4)

        def setTestSettings():
            name = nameEntry.get()
            if name == "":
                messagebox.showerror("Error", "Test name cannot be empty.", parent=t)
                return

            self.name = name
            self.notes = notes.get("1.0", END)
            if self.filename == "":
                result = messagebox.askquestion("No output file", "No output file selected. Proceed without saving?", icon='warning', parent=t)
                if result == "no":
                    return
            t.destroy()

        Button(fr, text="Done", command=setTestSettings).pack(side=RIGHT)

        t.protocol("WM_DELETE_WINDOW", setTestSettings)
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
        Label(fr, text="Sensor Name: ").grid(row=0, column=0, padx=(0,4))
        Label(fr, text="Initial thickness (mm): ").grid(row=0, column=1, padx=(4,0))
        for i in range(len(self.sensors)):
            e = Entry(fr)
            e.insert(0, self.sensorNames[i])
            nameentries.append(e)
            e.grid(row=i+1, column=0, pady=2, padx=(0,4))
            th = Entry(fr)
            th.insert(0, str(self.initialThicknesses[i]))
            thicknessentries.append(th)
            th.grid(row=i+1, column=1, pady=2, padx=(4,0))

        def updateSensorSettings():
            values = [entry.get() for entry in nameentries]
            #check sensors have unique names
            #could be done asymptotically faster w/ sorting or a map but we have like 4 sensors
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

        Button(fr, text="Save", command=updateSensorSettings).grid(row=len(self.sensors) + 1, column=1, sticky=E,  padx=(8,0), pady=(4,0))
        t.resizable(False, False)

        t.protocol("WM_DELETE_WINDOW", updateSensorSettings)
        t.grab_set()
        self.wait_window(t)

    def toShowDialog(self):
        t = Toplevel(self)
        paddingFrame = Frame(t)
        paddingFrame.pack(side=TOP, fill=BOTH, expand=True, padx=8, pady=8)
        for i in range(len(self.sensorNames)):
            Checkbutton(paddingFrame, text=self.sensorNames[i], variable=self.todisplay[i]).pack(side=TOP, pady=(0,4))
        Button(paddingFrame, text="Done", command=t.destroy).pack(side=TOP, anchor=E)

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

    def exportUnsavedReadings(self):
        if self.filename == "": #user has been warned, chose to proceed w/out saving
            return

        if self.nextUnsavedIndex is None:
            messagebox.showerror("No readings", "Please take some readings first.", parent=self)
            return

        elif self.nextUnsavedIndex >= len(self.currentPercentageSwelling[0]):
            return #all saved

        with open(self.filename, "a+") as f:
            f.seek(0, os.SEEK_END)
            for pointIndex in range(self.nextUnsavedIndex + 1, len(self.currentPercentageSwelling[0])):
                for sensorIndex in range(len(self.sensors)):
                    f.write(str(self.actualTimes[sensorIndex][pointIndex]) + " " + str(self.currentPercentageSwelling[sensorIndex][pointIndex])
                     + " " + str(self.currentVoltages[sensorIndex][pointIndex]) + " ")
                f.write("\n")

        self.nextUnsavedIndex = len(self.currentPercentageSwelling[0])


    def stopRecording(self):
        if self.animation is None:
            return

        self.exportUnsavedReadings()

        self.animation.event_source.stop()
        self.animation = None

        self.stopBtn.config(state=DISABLED)
        self.startBtn.config(state=NORMAL)
        self.timeEntry.config(state=NORMAL)
        self.rateEntry.config(state=NORMAL)

        self.progressLabel.config(text="Done.")
        self.progressBar["value"] = 0
        self.running = False

    def startRecording(self):
        if self.currentPercentageSwelling is not None:
            result = messagebox.askquestion("Results not exported", "Discard current readings?", icon='warning', parent=self)
            if result == "no":
                return

        if self.filename == "":
            result = messagebox.askquestion("No output file", "No output file has been selected. Proceed without saving?", icon='warning', parent=self)
            if result == "no":
                return

        t = tools.getFloatFromEntry(self, self.timeEntry, "Duration", mini=0)
        rate = tools.getFloatFromEntry(self, self.rateEntry, "Readings/minute", mini=0.01, maxi=130)

        if t is None or rate is None:
            return

        self.running = True

        self.menubar.entryconfig("Settings", state="disabled")

        rate = self.lastrate = 60000/rate

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

        if self.filename != "":
            try:
                with open(self.filename, "w") as f:
                    f.write(self.name + "\n" + time.ctime() + "\n" + str(time.time()) + "\nNotes:\n")
                    notes = self.notes.translate(str.maketrans({"\\": r"\\"}))
                    f.write(notes + "\n\\\n")
                    f.write("# sensors: " + str(len(self.sensors)) + "\n")
                    f.write("Sensor names:\n")
                    for name in self.sensorNames:
                        f.write(name + "\n")
                    f.write("Initial thicknesses(mm) - Initial displacement:\n")
                    for i in range(len(self.sensors)):
                        f.write(str(self.initialThicknesses[i]) + " - " + str(self.initialReadings[i]) + "\n")
                    f.write("For each sensor: Time(m) - Displacement(%) - Voltage(V)\n")
            except Exception as e:
                messagebox.showerror("Error", "Could not open '" + self.filename + "' to export", parent=self)
                self.filename = ""
                self.stopRecording()
                raise e
        
        multipliers = [100/self.initialThicknesses[i] for i in range(len(self.sensors))] #pre-compute conversion constant into percentage swelling
        self.currentPercentageSwelling = [[] for _ in range(len(self.sensors))]
        self.currentVoltages = [[] for _ in range(len(self.sensors))]
        self.actualTimes = [[] for _ in range(len(self.sensors))]
        self.progressBar.config(maximum=t)
        self.updateAxis = False

        def takeSingleResult(_):
            if not self.running:
                return self.plots
            moment = time.time()
            if (moment - self.lastSaveTime) > 300: #save everything after 5 mins
                self.exportUnsavedReadings()
                self.lastSaveTime = moment

            mins = (moment - self.lastStartTime) / 60
            
            self.progressBar["value"] = mins
            self.progressLabel.config(text = str(round(mins/t * 100, 2)) + "%")

            for i in range(len(self.sensors)):
                d, v = self.getCurrentDisplacementVoltage(i)
                d = self.initialReadings[i] - d
                percentage = d * multipliers[i]
                if (percentage > self.maxY):
                    self.maxY = percentage + 10
                    self.graph.set_ylim([0, self.maxY])
                    self.updateAxis = True

                self.currentPercentageSwelling[i].append(percentage)
                self.currentVoltages[i].append(v)
                thistime = (time.time() - self.lastStartTime) / 60
                self.actualTimes[i].append(thistime)
                plot = self.plots[i]
                if self.todisplay[i].get() == 1:
                    if thistime > self.maxX:
                        self.maxX = min(self.maxX * 2, t)
                        self.graph.set_xlim([0, self.maxX])
                        self.updateAxis = True
                    plot.set_data(self.actualTimes[i], self.currentPercentageSwelling[i])
                else:
                    plot.set_data([], [])

            if mins >= t:
                self.stopRecording()

            if self.updateAxis:
                self.canvas.draw()
                self.updateAxis = False

            return self.plots

        self.lastStartTime = time.time()
        self.lastSaveTime = self.lastStartTime
        self.nextUnsavedIndex = 0
        self.animation = matplotlib.animation.FuncAnimation(self.fig, takeSingleResult, interval=rate, blit=True, repeat=False)
        self.canvas.show()

    def launchOutputWindow(self):
        if self.outputWindow is None or not self.outputWindow.winfo_exists(): #closed or was never opened
            self.outputWindow = tools.DAQRawOutputDialog(self, self.connection)
            self.outputWindow.mainloop()
        else:
            self.outputWindow.lift()

    def getCurrentDisplacementVoltage(self, i):
        v = self.connection.read(self.sensors[i])
        m, b = self.paramList[i]
        return  [m * v + b, v]

    def initGraphFrame(self, fr):
        f = plt.figure(figsize=(8, 5), dpi=100)
        #plt.ion()
        self.fig = f
        a = f.add_subplot(111)
        a.set_xlabel("Time (m)")
        a.set_ylabel("Relative swell (%)")
        self.maxX = 1
        self.maxY = 150
        a.set_xlim([0,self.maxX])
        a.set_ylim([0,self.maxY])
        self.plots = []
        for i in range(len(self.sensors)):
            l, = a.plot([], label=self.sensorNames[i], animated=True)
            self.plots.append(l)
        h, l = a.get_legend_handles_labels()
        a.legend(h, l)
        self.graph = a

        wrapper = Frame(fr, relief=SUNKEN, borderwidth=1)
        canvas = FigureCanvasTkAgg(f, wrapper)
        canvas.show()
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        self.canvas = canvas

        return wrapper

    def fin(self):
        if self.animation: #still recording
            result = messagebox.askquestion("Test in progress", "Stop testing?", icon='warning', parent=self)
            if result == "no":
                return
            self.stopRecording()

        if self.currentPercentageSwelling is not None:
            self.exportUnsavedReadings()

        if self.outputWindow is not None and self.outputWindow.winfo_exists():
            self.outputWindow.destroy()
        self.destroy()

if __name__ == '__main__':
    print("Run main.py")

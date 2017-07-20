from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *
from tkinter import font
#import numpy as np
import scipy.stats
import tools
import matplotlib
import datetime
import settings
from numpy import argsort

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

#daq 6210

class CalibrationWindow(Toplevel):
    def __init__(self, master=None):
        Toplevel.__init__(self, master)
        self.title("Swellometer calibration")
        self.connection = tools.DAQInput()
        self.resizable(False, False)

        #used by tkinter to update labels
        self.readoutAfterID = None
        self.measurementAfterID = None
        self.results = [CalibrationWindow.SensorList(i) for i in range(settings.numsensors)]
        self.resListPointers = {} #treeview ids -> CalibrationResult
        self.finalParams = None #used by other windows to check if the user calibrated successfully
        self.parametersExported = False
        self.outputWindow = None

        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Export calibration parameters", command=self.exportParameters)
        filemenu.add_command(label="Export raw readings", command=self.exportReadings)
        filemenu.add_command(label="Exit", command=self.fin)
        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Sensor outputs", command=self.launchOutputWindow)
        menubar.add_cascade(label="File", menu=filemenu)
        menubar.add_cascade(label="View", menu=viewmenu)
        self.config(menu=menubar)

        self.plotColours = ["red", "blue", "black", "green"]

        self.protocol('WM_DELETE_WINDOW', self.fin)

        self.initwindow()

    def switchEntry(self, i=None):
        if i is None:
            for s in range(settings.numsensors):
                self.switchEntry(s)
        else:
            if self.sensorCheckedVars[i].get() == 1:
                self.sensorEntries[i].config(state=NORMAL)
            else:
                self.sensorEntries[i].config(state=DISABLED)

    def initwindow(self):
        mainFrame = Frame(self)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True)

        leftFrame = Frame(mainFrame)
        leftFrame.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)

        inputFrame = Frame(leftFrame)
        inputFrame.grid(row=0, column=0, rowspan=3, columnspan=3)

        self.sensorEntries = []
        self.sensorCheckedVars = []
        self.checkbuttons = []

        for i in range(settings.numsensors):
            var = IntVar()
            var.set(1)
            self.sensorCheckedVars.append(var)
            checkbutton = Checkbutton(inputFrame, text="Distance " + str(i+1) + " (mm): ", width=20, variable=var,
                                                command=lambda i=i: self.switchEntry(i))
            checkbutton.grid(row=i, column=0, pady=4)
            self.checkbuttons.append(checkbutton)
            entry = Entry(inputFrame)
            entry.grid(row=i, column=1, padx=5)
            self.sensorEntries.append(entry)

        readingsL = Label(inputFrame, text="Total # of readings: ", width=20)
        readingsL.grid(row=settings.numsensors, column=0, pady=4)
        readingsEntry = Entry(inputFrame)
        readingsEntry.insert(0, "10")
        readingsEntry.grid(row=4, column=1, padx=5)
        self.readingsEntry = readingsEntry

        rateL = Label(inputFrame, text="Readings/second: ", width=20)
        rateL.grid(row=settings.numsensors + 1, column=0, pady=4)
        rateEntry = Entry(inputFrame)
        rateEntry.insert(0, "2")
        rateEntry.grid(row=5, column=1)
        self.rateEntry = rateEntry

        measurementFrame = Frame(leftFrame)
        measurementFrame.grid(row=4, column=0, rowspan=5, columnspan=3)
        self.measurementFrame = measurementFrame

        cancelBtn = Button(measurementFrame, text="Cancel", command=self.stopReadings)
        cancelBtn.grid(row=0, column=0, padx=2, pady=(10,2))
        cancelBtn.config(state=DISABLED)
        self.cancelBtn = cancelBtn
        startBtn = Button(measurementFrame, text="Start", command=self.startReadings)
        startBtn.grid(row=0, column=1, padx=2, pady=(10,2))
        self.startBtn = startBtn

        curNumTaken = Label(measurementFrame, text="Readings taken: 0")
        curNumTaken.grid(row=1, column=0, columnspan=2, pady=(2,10))
        self.curNumTaken = curNumTaken

        listFrame = Frame(leftFrame, width=50)
        listFrame.grid(row=10, rowspan=13, column=0, columnspan=3, sticky=N + S + W + E)
        leftFrame.rowconfigure(10, weight=1)
        scrollbar = Scrollbar(listFrame)
        resList = Treeview(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED, columns=("distance", "mean", "std"))
        scrollbar.config(command=resList.yview)
        resList["show"] = "headings"
        resList.heading("distance", text="Distance (mm)")
        resList.column("distance", minwidth=10, width=50)
        resList.heading("mean", text="Mean (mV)")
        resList.column("mean", minwidth=10, width=50)
        resList.heading("std", text="Std.Dev. (mV)")
        resList.column("std", minwidth=10, width=50)

        class ResListPopup(Menu):
            def __init__(self, master):
                Menu.__init__(self, master, tearoff=0)
                self.master = master
                self.iid = None
                self.add_command(label="Remove", command=lambda: self.master.deleteReading(self.iid))

            def popup(self, x, y, iid):
                self.iid = iid
                self.tk_popup(x, y)

            def deleteObject(self):
                self.master.deleteReading(self.iid)
                
        self.resListPopup = ResListPopup(self)

        def resListRightClick(event):
            iid = resList.identify_row(event.y)
            if iid and resList.item(iid)["tags"] == '': #is not a 'sensor' header
                resList.selection_set(iid)
                self.resListPopup.popup(event.x_root, event.y_root, iid)
            else:
                pass
            
        resList.bind("<Button-3>", resListRightClick)
                
        titleFont = font.Font(family='Helvetica', size=10, weight='bold')
        resList.tag_configure("title", font=titleFont)

        self.sensorTreeviewIDs = []
        for i in range(settings.numsensors):
            id = resList.insert("", "end", i, values=("Sensor" + str(i + 1)), open=True, tags=("title",))
            self.sensorTreeviewIDs.append(id)
        resList.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=resList.yview)

        scrollbar.pack(side=RIGHT, fill=Y)
        self.resList = resList

        graph = self.initGraphFrame(mainFrame)
        graph.pack(side=RIGHT, fill=BOTH, expand=True, padx=8, pady=8)

        bottomBtnFrame = Frame(self)
        bottomBtnFrame.pack(side=BOTTOM, fill=X, padx=8, pady=(0,4))
        exitBtn = Button(bottomBtnFrame, text="Done", command=self.fin)
        exitBtn.pack(side=RIGHT)

    def launchOutputWindow(self):
        if self.outputWindow is None or not self.outputWindow.winfo_exists(): #closed or was never opened
            self.outputWindow = tools.DAQRawOutputDialog(self, self.connection)
            self.outputWindow.mainloop()
        else:
            self.outputWindow.lift()
            
    class CalibrationResult:
        def __init__(self, dist, inductionList, sensor):
            self.dist = dist
            self.sensor = sensor
            self.num = len(inductionList)
            self.inductionList = inductionList
            self.mean = sum(inductionList) / len(inductionList)
            self.SD = scipy.std(inductionList)
            self.iid = None

        def toStr(self):
            return str(self.dist) + "mm    -    " + str(round(self.mean,3)) + "mV    -    SD " + str(round(self.SD, 3)) + "mV"

        def export(self):
            string = "Distance: " + str(self.dist) + "mm\n"
            string += "Calculated mean: " + str(self.mean) + "\tCalculated SD: " + str(self.SD) + '\n'
            string += "Num points: " + str(len(self.inductionList)) + "\n"
            string += "DAQ inputs:\n"
            for i in range(len(self.inductionList)):
                string += str(i) + " - " + str(self.inductionList[i]) + "\n"
            return string
        
        def merge(self, merginglist): #absorb a list of readings and update stats
            self.inductionList += merginglist
            self.num = len(self.inductionList)
            self.mean = sum(self.inductionList) / len(self.inductionList)
            self.SD = scipy.std(self.inductionList)

    class SensorList:
        def __init__(self, sensornum):
            self.distances = []
            self.results = []
            self.sensornum = sensornum

        #inserts/merges and returns the result object
        def insert(self, distance, voltageList):
            #could be done with a heap but there is going to be max 20 readings per sensor
            for i in range(len(self.distances)):
                if distance == self.distances[i]:
                    self.results[i].merge(voltageList)
                    return self.results[i]

                if distance < self.distances[i]:
                    self.distances.insert(i, distance)
                    self.results.insert(i, CalibrationWindow.CalibrationResult(distance, voltageList, self.sensornum))
                    return self.results[i]

            self.distances.append(distance)
            result = CalibrationWindow.CalibrationResult(distance, voltageList, self.sensornum)
            self.results.append(result)
            return result

        def delete(self, distance):
            index = self.distances.index(distance)
            del self.distances[index]
            del self.results[index]

        def getPointsSortedByDistance(self):
            return self.distances, [result.mean for result in self.results]

        #used finally when exporting parameters
        def getPointsSortedByVoltage(self):
            voltages = [result.mean for result in self.results]
            sortedIndicies = argsort(voltages)
            return [voltages[i] for i in sortedIndicies], [self.distances[i] for i in sortedIndicies]

    def deleteReading(self, iid):
        self.resList.delete(iid)
        res = self.resListPointers[iid]
        self.results[res.sensor].delete(res.dist)
        self.replot()

    def exportReadings(self):
        f = filedialog.asksaveasfile(mode='w', parent=self)
        if f is not None:
            f.write("Calibration report - " + str(datetime.datetime.now()) + "\n")
            for s in range(settings.numsensors):
                results = self.results[s].results
                string = "\n***Sensor " + str(s+1) + "***\n"
                string += "Total # of distinct distances: " + str(len(results)) + "\n"
                for i in range(len(results)):
                    string += "---Reading " + str(i) + "---\n"
                    string += results[i].export()
                f.write(string)
            f.close()

    def enableSensors(self, enable=True):
        (setting, antisetting) = (NORMAL, DISABLED) if enable else (DISABLED, NORMAL)
        self.cancelBtn.config(state=antisetting)
        self.startBtn.config(state=setting)
        for checkbutton in self.checkbuttons:
            checkbutton.config(state=setting)
        for entry in self.sensorEntries:
            entry.config(state=setting)
        self.rateEntry.config(state=setting)
        self.readingsEntry.config(state=setting)

        if enable:
            self.switchEntry()

    def startReadings(self):
        toRecord = [] #some sensors will be disabled (via checkbuttons)
        distances = []
        for i in range(settings.numsensors):
            if self.sensorCheckedVars[i].get() == 1:
                toRecord.append(i)
                d = tools.getFloatFromEntry(self, self.sensorEntries[i], "Sensor " + str(i+1), mini=0.1)
                if d is None:
                    return
                distances.append(d)

        if len(toRecord) == 0:
            messagebox.showerror("No sensors", "Please enable some sensors first!", parent=self)
            return

        rate = tools.getFloatFromEntry(self, self.rateEntry, "Rate Entry", mini=0, maxi=4)
        totalNo = tools.getFloatFromEntry(self, self.readingsEntry, "# of readings", mini=1, forceInt=True)
        if (rate is None or totalNo is None):
            return

        self.enableSensors(False)

        rate = int(1000/rate)
        totalNo = int(totalNo)
        currentReadings = [[] for i in range(len(toRecord))]
        self.curNumTaken.config(text="Readings taken: 0/" + str(totalNo))

        def addResults():
            self.parametersExported = False
            self.stopReadings()
            for i in range(len(toRecord)):
                sensor = toRecord[i]
                distance = distances[i]
                
                if distance > self.maxX:
                    self.maxX = distance + 1
                
                res = self.results[sensor].insert(distance, currentReadings[i])
                
                if res.mean > self.maxY:
                    self.maxY = res.mean + 1

                res.iid = self.resList.insert(self.sensorTreeviewIDs[sensor], "end", values=(distance, res.mean, round(res.SD, 3)))
                self.resListPointers[res.iid] = res
                
                self.sensorEntries[sensor].delete(0, "end")
                

            self.replot()

        def takeSingleReading():
            if len(currentReadings[0]) == totalNo:
                addResults()
                self.stopReadings()
                return

            for i in range(len(toRecord)):
                r = self.connection.read(toRecord[i])
                currentReadings[i].append(r)

            self.curNumTaken.config(text="Readings taken: " + str(len(currentReadings[0])) + "/" + str(totalNo))
            self.measurementAfterID = self.measurementFrame.after(rate, takeSingleReading)

        takeSingleReading()

    def stopReadings(self):
        self.enableSensors(True)

        if self.measurementAfterID is not None:
            self.measurementFrame.after_cancel(self.measurementAfterID)
            self.measurementAfterID = None

        self.curNumTaken.config(text="Readings taken: 0")

    def initGraphFrame(self, fr):
        f = Figure(figsize=(8, 5), dpi=100)
        a = f.add_subplot(111)
        a.set_xlabel("Distance (mm)")
        a.set_ylabel("Inductance (mV)")
        self.maxX = 10
        self.maxY = settings.maxDAQoutput
        a.set_xlim([0,self.maxX])
        a.set_ylim([0,self.maxY])
        self.graph = a

        wrapper = Frame(fr, relief=SUNKEN, borderwidth=1)
        canvas = FigureCanvasTkAgg(f, wrapper)
        canvas.show()
        self.canvas = canvas

        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        return wrapper

    def replot(self):
        self.graph.clear()

        self.graph.set_xlim([0, self.maxX])
        self.graph.set_ylim([0, self.maxY])

        for s in range(settings.numsensors):
            xs, ys = self.results[s].getPointsSortedByDistance()
            if len(xs) == 0:
                continue
            self.graph.scatter(xs, ys, c=self.plotColours[s], label="Sensor " + str(s+1))
            if len(xs) > 1:
                self.graph.plot(xs, ys, c=self.plotColours[s])

        self.graph.set_xlabel("Distance (mm)")
        self.graph.set_ylabel("Inductance (mV)")

        h,l = self.graph.get_legend_handles_labels()
        self.graph.legend(h,l)

        self.canvas.draw()

    def exportParameters(self):
        f = filedialog.asksaveasfile(mode='w', parent=self, defaultextension=".calib", filetypes=[("Calibration File", "*.calib")])
        if f is not None:
            parameters = self.getParameters()
            for sensor in parameters:
                f.write(str(sensor[0]) + "\n")
                for x, y in sensor[1:]:
                    f.write (str(x) + " " + str(y) + "\n")

    #returns [[sensornum, [x0, y0]...]...]
    def getParameters(self):
        sensors = []
        for i in range(settings.numsensors):
            xs, ys = self.results[i].getPointsSortedByVoltage()
            if len(xs) >= 2:
                sensors.append([i] + [[xs[i], ys[i]] for i in range(len(xs))])
        return sensors

    def fin(self):
        good = False  # there exists a sensor with enough readings
        for i in range(settings.numsensors):
            if len(self.results[i].distances) > 1:
                good = True
                break
        if not good:
            result = messagebox.askquestion("Not enough points",
                                            "No sensors have enough readings. Quit?",
                                            icon='warning', parent=self)
            if result == 'yes':
                self.destroy()
            return

        bad = False  # there exists a sensor without enough readings
        for i in range(settings.numsensors):
            if len(self.results[i].distances) < 2:
                bad = True
                break

        if bad:
            result = messagebox.askquestion("Not enough points",
                                            "Some sensors do not have enough distinct readings. Continue anyway?",
                                            icon='warning', parent=self)
            if result == "no":
                return False

        if not self.parametersExported:
            res = messagebox.askyesno("Parameters not saved", "Do you want to save the calibration parameters?", parent=self)
            if res:
                self.exportParameters()

        self.finalParams = self.getParameters()
        if self.outputWindow is not None and self.outputWindow.winfo_exists():
            self.outputWindow.destroy()
        self.destroy()
        
if __name__ == '__main__':
    print("Run main.py")

import time
import os
import analysisgraph
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font
from tkinter.ttk import *

class AnalysisWindow(Toplevel):
    def __init__(self):
        Toplevel.__init__(self)
        self.title("Swellometer Analysis")
        self.loadedRuns = {} #(runname, runtime) -> (listID, runObject)
        self.graphmode = StringVar(self)
        self.graphmode.set("Percentage Displacement")
        self.filtermode = IntVar(self)
        self.filtermode.set(0)
        self.resizable(False, False)
        self.initwindow()

    def initwindow(self):
        mainFrame = Frame(self)
        mainFrame.pack(fill=BOTH, padx=8, pady=8)

        self.graph = analysisgraph.AnalysisGraph(mainFrame)
        self.graph.pack(side=RIGHT, fill=BOTH, expand=True)

        leftFrame = Frame(mainFrame)
        leftFrame.pack(side=LEFT, fill=Y, expand=True, padx=(0, 8))

        listFrame = Frame(leftFrame, width=400)
        listFrame.pack(side=TOP, fill=Y, expand=True)
        scrollbar = Scrollbar(listFrame)
        importList = Treeview(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED, columns=("name", "points"))
        scrollbar.config(command=importList.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        importList["show"] = "headings"
        importList.heading("name", text="Name")
        importList.column("name", minwidth=3000, width=300)
        importList.heading("points", text="# points")
        importList.column("points", minwidth=10, width=100)
        importList.pack(side=LEFT, fill=BOTH, expand=True)

        self.indexPointers = {} #treeview iid -> sensor/run
        def importListDoubleClick(event):
            item = importList.identify('item',event.x,event.y)
            pointed = self.indexPointers[item]
            if "runname" in pointed: #doubleclicked run
                self.runInfoDialog(pointed)
            else:
                self.sensorInfoDialog(pointed)

        class ImportListPopup(Menu):
            def __init__(self, master):
                Menu.__init__(self, master, tearoff=0)
                self.master = master
                self.id = None
                self.add_command(label="More...", command=self.showInfoDialog)
                self.add_command(label="Remove", command=self.deleteObject)

            def popup(self, x, y, id):
                self.id = id
                self.tk_popup(x, y)

            def showInfoDialog(self):
                pointed = self.master.indexPointers[self.id]
                if "runname" in pointed:
                    self.master.runInfoDialog(pointed)
                else:
                    self.master.sensorInfoDialog(pointed)

            def deleteObject(self):
                self.master.deleteObject(self.id)
        self.importPopup = ImportListPopup(self)

        def importListRightClick(event):
            iid = importList.identify_row(event.y)
            if iid:
                importList.selection_set(iid)
                self.importPopup.popup(event.x_root, event.y_root, iid)
            else:
                pass

        importList.bind("<Double-1>", importListDoubleClick)
        importList.bind("<Button-3>", importListRightClick)

        runFont = font.Font(family='Helvetica', size=10, weight='bold')
        importList.tag_configure("run", font=runFont)
        self.importList = importList

        Button(leftFrame, text="Import...", command=self.importData).pack(side=RIGHT, pady=(4,0))

        OptionMenu(leftFrame, self.graphmode, "Percentage displacement", "Percentage displacement", 
            "Average percentage displacement", "Voltages", "Swelling rate", "Average swelling rate", "Total swell", command=self.setGraphMode).pack(side=LEFT, pady=(4, 0))
        Checkbutton(leftFrame, text="Smooth graph",  variable=self.filtermode, command=self.setFilterMode).pack(side=LEFT, padx=(4,0), pady=(4, 0))
        self.setGraphMode()
        self.mainloop()

    #def setGraphLimits

    def setGraphMode(self, _=None):
        runs = [run for _, (_, run) in self.loadedRuns.items()]
        selection = self.graphmode.get()
        if selection == "Percentage displacement":
            self.graph.plotDistances(runs)
        elif selection == "Voltages":
            self.graph.plotVoltages(runs)
        elif selection == "Total swell":
            self.graph.plotTotalSwells(runs)
        elif selection == "Swelling rate":
            self.graph.plotRatePercentageSwell(runs)
        elif selection == "Average percentage displacement":
            self.graph.plotAverageDistance(runs)
        elif selection == "Average swelling rate":
            self.graph.plotAverageSwellingRate(runs)
        else:
            self.graph.clear()
            self.graph.draw()

    def setFilterMode(self):
        self.graph.tofilter = self.filtermode.get() == 1
        self.setGraphMode()

    def deleteObject(self, iid, warn=True):
        pointed = self.indexPointers[iid]
        if "runname" in pointed:
            if warn:
                res = messagebox.askyesno("Delete run", "Are you sure you want to remove this run and all of its data?", parent=self)
                if res == "no":
                    return
            for i in self.importList.get_children(iid):
                del self.indexPointers[i]
                self.importList.delete(i)
            del self.loadedRuns[(pointed["runname"], pointed["timeofrun"])]
        else:
            parentRun = self.indexPointers[self.importList.parent(iid)]
            del parentRun["sensors"][pointed["name"]]
        self.importList.delete(iid)
        del self.indexPointers[iid]
        self.setGraphMode()

    def setGraphAxis(self):
        t = Toplevel(self)
        paddingFrame = Frame(t)
        paddingFrame.pack(side=TOP, padx = 8, pady = 8)

        xoptions = Frame(paddingFrame)


    def runInfoDialog(self, run):
        t = Toplevel(self)
        frame = Frame(t)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        Label(frame, text="Name: " + run["runname"]).pack(side=TOP)
        Label(frame, text="Time: " + time.strftime("%a, %d %b %Y %H:%M:%S", run["timeofrun"])).pack(side=TOP)
        Label(frame, text="Notes:", anchor=W, justify=LEFT, width=50, wraplength=300).pack(side=TOP)
        Label(frame, text=run["notes"], justify=LEFT, wraplength=300, borderwidth=1, relief="sunken").pack(side=TOP, fill=X, expand=True)

        listbox = Listbox(frame, height=0)

        for name, sensor in run["sensors"].items():
            listbox.insert(END, name)

        def listDoubleClick(_):
            pointed = run["sensors"][listbox.selection_get()]
            self.sensorInfoDialog(pointed)

        listbox.pack(side=TOP, fill=X, expand=True, pady=4)
        listbox.bind("<Double-1>", listDoubleClick)

        Button(frame, text="OK", command=t.destroy).pack(side=RIGHT, pady=(4,0))
        t.resizable(False, False)
        t.mainloop()

    def sensorInfoDialog(self, sensor):
        t = Toplevel(self)
        frame = Frame(t)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        Label(frame, text="Name: " + sensor["name"]).pack(side=TOP)
        Label(frame, text="# of readings: " + str(len(sensor["times"]))).pack(side=TOP)
        Label(frame, text="Initial sample thickness (mm): " + str(sensor["initialThickness"])).pack(side=TOP)
        Label(frame, text="Initial displacement (mm): " + str(sensor["initialDisplacement"])).pack(side=TOP)

        listFrame = Frame(frame, width=300)
        listFrame.pack(side=TOP)
        scrollbar = Scrollbar(listFrame)
        resList = Treeview(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED, columns=("time", "distance", "voltage"))
        scrollbar.config(command=resList.yview)
        resList["show"] = "headings"
        resList.heading("time", text="Time (m)")
        resList.column("time", minwidth=10, width=100)
        resList.heading("distance", text="Displacement (%)")
        resList.column("distance", minwidth=10, width=100)
        resList.heading("voltage", text="Voltage (mV)")
        resList.column("voltage", minwidth=10, width=100)

        for i in range(len(sensor["times"])):
            resList.insert("", "end", i, values=(sensor["times"][i], sensor["pdisplacements"][i], sensor["voltages"][i]))

        resList.pack(side=LEFT, fill=BOTH, expand=True, pady=4)
        scrollbar.config(command=resList.yview)
        scrollbar.pack(side=RIGHT, fill=Y, pady=4)

        Button(frame, text="OK", command=t.destroy).pack(side=RIGHT)
        t.resizable(False, False)
        t.mainloop()

    def chooseSensorsDialogue(self, names, filename):
        t = Toplevel(self)
        paddingFrame = Frame(t)
        paddingFrame.pack(fill=BOTH, expand=True, padx = 8, pady = 8)
        t.title("Import sensor data")
        Label(paddingFrame, text="Import from '" + os.path.basename(filename) + "'").pack(side=TOP)
        self.checkboxVars = [IntVar() for _ in names]
        self.checkbuttons = []
        for n in range(len(names)):
            c = Checkbutton(paddingFrame, text=names[n], variable=self.checkboxVars[n])
            self.checkboxVars[n].set(1)
            c.pack(side=TOP, pady=4)

        t.resizable(False, False)
        Button(paddingFrame, text="Import", command=t.destroy).pack(side=TOP)

        self.wait_window(t)
        return [n.get() == 1 for n in self.checkboxVars]

    def importData(self):
        filenames = filedialog.askopenfilenames(parent=self, defaultextension=".data", filetypes=[("Data File", "*.data")])
        if not filenames:
            return

        runs = []
        for filename in filenames:
            try:
                with open(filename, "r") as f:
                    runname = f.readline()[:-1]

                    f.readline() #throw away human-readable date
                    timeofrun = time.localtime(float(f.readline()[:-1]))

                    if (runname, timeofrun) in self.loadedRuns:
                        res = messagebox.askyesno("Reload run", "Do you want to reload '" + runname + "'?", parent=self)
                        if res == "no":
                            continue
                        else:
                            iid, _ = self.loadedRuns[(runname, timeofrun)]
                            self.deleteObject(iid, warn=False)
                    f.readline() #'Notes:'
                    notes = ""
                    while True: #notes are delimited by single backslash
                        c = f.read(1)
                        if not c:
                            raise ValueError("Unexpected EOF")
                        if c == '\\':
                            c = f.read(1)
                            if c == '\\':
                                notes += '\\'
                            else:
                                break
                        notes += c
                    numsensors = int(f.readline().split()[2])
                    f.readline() #Sensor names:
                    sensors = [{"name": f.readline()[:-1], "times":[], "pdisplacements":[], "voltages":[]} for _ in range(numsensors)]
                    f.readline() #"Initial thicknesses(mm) - Initial displacements(mm):
                    for i in range(numsensors):
                        thicc, _, displacement = f.readline().split()
                        sensors[i]["initialThickness"] = float(thicc)
                        sensors[i]["initialDisplacement"] = float(displacement)
                    f.readline() #'Time(m) - Displacement(%) - Voltage(V)'
                    f.readline() #newline

                    line = f.readline()
                    while line:
                        data = line.split()
                        for i in range(0, numsensors):
                            index = i*3
                            sensors[i]["times"].append(float(data[index]))
                            sensors[i]["pdisplacements"].append(float(data[index+1]))
                            sensors[i]["voltages"].append(float(data[index+2]))
                        line = f.readline()

                    toimport = self.chooseSensorsDialogue([sensors[i]["name"] for i in range(numsensors)], filename)
                    sensors = {sensors[i]["name"]:sensors[i] for i in range(numsensors) if toimport[i]}
                    runs.append({"runname": runname, "timeofrun": timeofrun, "sensors": sensors, "notes":notes})
            except Exception as e:
                messagebox.showerror("Error", "Could not import data from '" + os.path.basename(filename) + "'.")
                raise e

        for run in runs:
            rootid = self.importList.insert("", "end", values=(str(len(self.loadedRuns) + 1) + " - " + run["runname"], ""), open=True, tags=("run"))
            self.loadedRuns[(run["runname"], run["timeofrun"])] = [rootid, run]
            self.indexPointers[rootid] = run
            for name, sensor in run["sensors"].items():
                self.indexPointers[self.importList.insert(rootid, "end", values=(name, str(len(sensor["times"]))))] = sensor

        self.setGraphMode()
    
if __name__ == "__main__":
    AnalysisWindow()

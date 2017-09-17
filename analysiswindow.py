import os
import shutil
import time
from tempfile import mkstemp
from tkinter import *
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox
from tkinter.ttk import *

import analysisgraph
import reportgen
import tools
import xlwt

class AnalysisWindow(Toplevel):
    def __init__(self):
        Toplevel.__init__(self)
        self.title("Swellometer Analysis")
        self.loadedRuns = {}  # (runname, runtime) -> (listID, runObject)
        self.graphmode = StringVar(self)
        self.graphmode.set("Percentage Displacement")
        self.filtermode = IntVar(self)
        self.filtermode.set(0)
        self.resizable(False, False)
        self.initwindow()

    def initwindow(self):
        mainFrame = Frame(self)
        mainFrame.pack(fill=BOTH, padx=8, pady=8)
        self.mainFrame = mainFrame

        self.graph = analysisgraph.AnalysisGraph(mainFrame)
        self.graph.pack(side=RIGHT, fill=BOTH, expand=True)

        leftFrame = Frame(mainFrame)
        leftFrame.pack(side=LEFT, fill=Y, expand=True, padx=(0, 8))

        listFrame = Frame(leftFrame, width=400)
        listFrame.pack(side=TOP, fill=Y, expand=True)
        scrollbar = Scrollbar(listFrame)
        importList = Treeview(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED, columns=("name", "show"))
        scrollbar.config(command=importList.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        importList["show"] = "headings"
        importList.heading("name", text="Name")
        importList.column("name", minwidth=300, width=300)
        importList.heading("show", text="Visible")
        importList.column("show", minwidth=60, width=60)
        importList.pack(side=LEFT, fill=BOTH, expand=True)

        self.indexPointers = {}  # treeview iid -> sensor/run

        def importListDoubleClick(event):
            item = importList.identify("item", event.x, event.y)
            if not item:
                return
            pointed = self.indexPointers[item]

            newdisplay = not pointed["toshow"]
            pointed["toshow"] = newdisplay
            value = "True" if newdisplay else "False"
            importList.set(item, column="show", value=value)

            if "runname" in pointed:  # doubleclicked run
                for child in importList.get_children(item):
                    self.indexPointers[child]["toshow"] = newdisplay
                    importList.set(child, column="show", value=value)

            self.setGraphMode()

        class ImportListPopup(Menu):
            def __init__(self, master):
                Menu.__init__(self, master, tearoff=0)
                self.master = master
                self.id = None
                self.add_command(label="More...", command=self.showInfoDialog)
                self.add_command(label="Remove", command=self.deleteObject)
                self.add_command(label="Rename...", command=self.renameObject)

            def popup(self, x, y, id):
                self.id = id
                self.tk_popup(x, y)

            def showInfoDialog(self):
                pointed = self.master.indexPointers[self.id]
                if "runname" in pointed:
                    self.master.runInfoDialog(pointed)
                else:
                    self.master.sensorInfoDialog(pointed)

            def renameObject(self):
                self.master.renameDialog(self.id)


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

        importList.bind("<Double-Button-1>", importListDoubleClick)
        importList.bind("<Button-3>", importListRightClick)

        runFont = font.Font(family='Helvetica', size=10, weight='bold')
        importList.tag_configure("run", font=runFont)
        self.importList = importList

        Button(leftFrame, text="Import...", command=self.importData).pack(side=RIGHT, pady=(4, 0))

        OptionMenu(leftFrame, self.graphmode, "Average percentage displacement", "Percentage displacement",
                   "Average percentage displacement", "Voltages", "Swelling rate", "Average swelling rate",
                   "Total swell", command=self.setGraphMode).pack(side=LEFT, pady=(4, 0))
        self.setGraphMode()

        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Import test", command=self.importData)
        filemenu.add_command(label="Export to Excel", command=self.exportToExcel)
        filemenu.add_command(label="Generate Report", command=self.genReport)
        filemenu.add_command(label="Clear loaded runs", command=self.clearImports)
        menubar.add_cascade(label="File", menu=filemenu)
        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Edit ranges", command=self.setGraphAxis)
        viewmenu.add_command(label="Fit model", command=self.fitModel)
        viewmenu.add_checkbutton(label="Smooth graph", variable=self.filtermode, command=self.setFilterMode)
        menubar.add_cascade(label="View", menu=viewmenu)

        self.menubar = menubar
        self.config(menu=menubar)

        self.mainloop()

    def exportToExcel(self):
        runs = [run for _, (_, run) in self.loadedRuns.items()]

        book = xlwt.Workbook(encoding="utf-8")

        boldstyle = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True
        boldstyle.font = font
        forbiddenChars = "\/*[]:?"

        for run in runs:
            if any(c in run["runname"] for c in forbiddenChars):
                messagebox.showerror("Error", "Cannot export runs with names containing '" + forbiddenChars + "'", parent=self)
                return
            
            if len(run["runname"]) > 30:
                sheetname = run["runname"][:30]
            else:
                sheetname = run["runname"]

            sheet = book.add_sheet(sheetname)
            sensors = list(run["sensors"].values())
            sheet.write(0,0, run["runname"], style=boldstyle)
            for i in range(len(sensors)):
                sensor = sensors[i]
                xindex = i * 4
                sheet.write(1, xindex, sensor["name"], style=boldstyle)
                sheet.write(2, xindex,"Time (m)")
                sheet.write(2, xindex + 1, "Swell(%)")
                sheet.write(2, xindex + 2, "Voltage (V)")
                for j in range(len(sensor["times"])):
                    sheet.write(j+3, xindex, str(sensor["times"][j]))
                    sheet.write(j+3, xindex + 1, str(sensor["pdisplacements"][j]))
                    sheet.write(j+3, xindex + 2, str(sensor["voltages"][j]))

        filename = filedialog.asksaveasfilename(parent=self, defaultextension=".xls")
        book.save(filename)

    def fitModel(self):
        t = Toplevel(self)
        t.title("Fit ranges")
        t.grab_set()
        t.resizable(False, False)
        paddingFrame = Frame(t)
        paddingFrame.pack(padx=8, pady=8)
        Label(paddingFrame, text="x begin (m): ").grid(row=0, column=0, sticky=W)
        xbeginEntry = Entry(paddingFrame)
        xbeginEntry.insert(0, "0")
        xbeginEntry.grid(row=0, column=1)
        Label(paddingFrame, text="x end (m): ").grid(row=1, column=0, sticky=W, pady=(4, 0))
        xendEntry = Entry(paddingFrame)
        xendEntry.grid(row=1, column=1, pady=(4, 0))

        xmin = xend = -1

        def setRange():
            nonlocal xmin
            nonlocal xend
            xmin = tools.getFloatFromEntry(self, xbeginEntry, "xmin")
            xend = tools.getFloatFromEntry(self, xendEntry, "xend")

            if xmin is None or xend is None:
                return
            elif xmin >= xend:
                messagebox.showerror("Error", "xmin must be less than xend", parent=self)
            else:
                t.destroy()

        Button(paddingFrame, text="Done", command=setRange).grid(row=2, column=1, sticky=E, pady=(4, 0))
        self.wait_window(t)
        if xend == -1:
            return
        tools.setAll(self.mainFrame, DISABLED)
        self.graph.fitModel([run for _, (_, run) in self.loadedRuns.items()], xmin, xend)
        tools.setAll(self.mainFrame, NORMAL)

    def setGraphMode(self, event=None):
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
            raise ValueError("Weird dropdown option")

    def setFilterMode(self):
        self.graph.tofilter = self.filtermode.get() == 1
        self.setGraphMode()

    def genReport(self):
        runs = [run for _, (_, run) in self.loadedRuns.items()]
        if len(runs) == 0:
            return
        foldername = filedialog.askdirectory()
        if foldername:
            try:
                if os.path.exists(foldername):
                    if not os.path.isdir(foldername) or os.listdir(foldername):  # is a file or is nonempty
                        if not messagebox.askyesno("Delete",
                                                   "'" + os.path.basename(foldername) + "' already exists. Delete?",
                                                   parent=self):
                            return

                    delName = tools.uniqueName(foldername + "deleting")
                    os.rename(foldername, delName)  # might not be deleted when we get to makedirs
                    shutil.rmtree(delName)
                options = reportgen.reportGenDialogue(runs, self)
                if options == {}:
                    return
                tools.setAll(self, DISABLED)
                reportgen.genReport(runs, options, foldername, self.graph)
            except Exception as e:
                messagebox.showerror("Error",
                                     "Failed to generate report. Please make sure nothing is using '" + os.path.basename(
                                         foldername) + "'", parent=self)
                raise e
            tools.setAll(self, NORMAL)

    def clearImports(self):
        res = messagebox.askyesno("Clear window", "Are you sure you want to clear this window?", parent=self)
        if not res:
            return
        self.importList.delete(*self.importList.get_children())
        self.indexPointers = {}
        self.loadedRuns = {}
        self.setGraphMode()

    def deleteObject(self, iid, warn=True):
        pointed = self.indexPointers[iid]
        if "runname" in pointed:
            if warn:
                res = messagebox.askyesno("Remove run", "Are you sure you want to remove this run and all of its data?",
                                          parent=self)
                if not res:
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
        t.title("Set axis")
        t.grab_set()
        paddingFrame = Frame(t)
        paddingFrame.pack(side=TOP, padx=8, pady=8)

        xmin, xmax, ymin, ymax = self.graph.getCurrentLims()
        xmaxEntry = Entry(paddingFrame)
        xmaxEntry.insert(0, xmax)
        xmaxEntry.grid(row=0, column=4)
        Label(paddingFrame, text="xmax:").grid(row=0, column=3, padx=(6, 0))
        xminEntry = Entry(paddingFrame)
        xminEntry.insert(0, xmin)
        xminEntry.grid(row=0, column=2)
        Label(paddingFrame, text="xmin:").grid(row=0, column=1, padx=(6, 0))
        xautoscale = IntVar()
        xautoscale.set(1 if self.graph.autoscaleX else 0)

        def xcheckclick():
            status = NORMAL if xautoscale.get() == 0 else DISABLED
            xminEntry.config(state=status)
            xmaxEntry.config(state=status)

        xcheckclick()

        Checkbutton(paddingFrame, text="Autoscale x", variable=xautoscale, command=xcheckclick).grid(row=0, column=0)

        ymaxEntry = Entry(paddingFrame)
        ymaxEntry.insert(0, ymax)
        ymaxEntry.grid(row=1, column=4, pady=(6, 0))
        Label(paddingFrame, text="ymax: ").grid(row=1, column=3, padx=(6, 0), pady=(6, 0))
        yminEntry = Entry(paddingFrame)
        yminEntry.insert(0, ymin)
        yminEntry.grid(row=1, column=2, pady=(6, 0))
        Label(paddingFrame, text="ymin: ").grid(row=1, column=1, padx=(6, 0), pady=(6, 0))
        yautoscale = IntVar()
        yautoscale.set(1 if self.graph.autoscaleY else 0)

        def ycheckclick():
            status = NORMAL if yautoscale.get() == 0 else DISABLED
            yminEntry.config(state=status)
            ymaxEntry.config(state=status)

        ycheckclick()

        Checkbutton(paddingFrame, text="Autoscale y", variable=yautoscale, command=ycheckclick).grid(row=1, column=0,
                                                                                                     pady=(6, 0))

        def save():
            if xautoscale.get() == 1:
                self.graph.autoscaleX = True
            else:
                self.graph.autoscaleX = False
                self.graph.xmin = tools.getFloatFromEntry(self, xminEntry, "xmin")
                self.graph.xmax = tools.getFloatFromEntry(self, xmaxEntry, "xmax")

            if yautoscale.get() == 1:
                self.graph.autoscaleY = True
            else:
                self.graph.autoscaleY = False
                self.graph.ymin = tools.getFloatFromEntry(self, yminEntry, "ymin")
                self.graph.ymax = tools.getFloatFromEntry(self, ymaxEntry, "ymax")
            self.graph.scaleToLims()
            self.setGraphMode()
            t.destroy()

        btnFrame = Frame(paddingFrame)
        btnFrame.grid(row=2, column=4, columnspan=1, sticky=E, pady=(4, 0))
        Button(btnFrame, text="Save", command=save).pack(side=RIGHT)
        Button(btnFrame, text="Cancel", command=t.destroy).pack(side=RIGHT, padx=(0, 4))
        t.resizable(False, False)
        t.grab_set()
        self.wait_window(t)

    def runInfoDialog(self, run):
        t = Toplevel(self)
        t.title("Run Information")
        frame = Frame(t)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        Label(frame, text="Name: " + run["runname"]).pack(side=TOP)
        Label(frame, text="Time: " + time.strftime("%a, %d %b %Y %H:%M:%S", run["timeofrun"])).pack(side=TOP)
        Label(frame, text="Notes:", anchor=W, justify=LEFT, width=50, wraplength=300).pack(side=TOP)
        Label(frame, text=run["notes"], justify=LEFT, wraplength=300, borderwidth=1, relief="sunken").pack(side=TOP,
                                                                                                           fill=X,
                                                                                                           expand=True)

        listbox = Listbox(frame, height=0)

        for name, sensor in run["sensors"].items():
            listbox.insert(END, name)

        def listDoubleClick(_):
            pointed = run["sensors"][listbox.selection_get()]
            self.sensorInfoDialog(pointed)

        listbox.pack(side=TOP, fill=X, expand=True, pady=4)
        listbox.bind("<Double-1>", listDoubleClick)

        Button(frame, text="OK", command=t.destroy).pack(side=RIGHT, pady=(4, 0))
        t.resizable(False, False)
        t.mainloop()

    def sensorInfoDialog(self, sensor):
        t = Toplevel(self)
        t.title("Sensor Information")
        frame = Frame(t)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        Label(frame, text="Name: " + sensor["name"]).pack(side=TOP)
        Label(frame, text="# of readings: " + str(len(sensor["times"]))).pack(side=TOP)
        Label(frame, text="Initial sample thickness (mm): " + str(sensor["initialThickness"])).pack(side=TOP)
        Label(frame, text="Initial displacement (mm): " + str(sensor["initialDisplacement"])).pack(side=TOP)

        listFrame = Frame(frame, width=300)
        listFrame.pack(side=TOP)
        scrollbar = Scrollbar(listFrame)
        resList = Treeview(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED,
                           columns=("time", "distance", "voltage"))
        scrollbar.config(command=resList.yview)
        resList["show"] = "headings"
        resList.heading("time", text="Time (m)")
        resList.column("time", minwidth=10, width=100)
        resList.heading("distance", text="Displacement (%)")
        resList.column("distance", minwidth=10, width=100)
        resList.heading("voltage", text="Voltage (V)")
        resList.column("voltage", minwidth=10, width=100)

        for i in range(len(sensor["times"])):
            resList.insert("", "end", i,
                           values=(sensor["times"][i], sensor["pdisplacements"][i], sensor["voltages"][i]))

        resList.pack(side=LEFT, fill=BOTH, expand=True, pady=4)
        scrollbar.config(command=resList.yview)
        scrollbar.pack(side=RIGHT, fill=Y, pady=4)

        Button(frame, text="OK", command=t.destroy).pack(side=RIGHT)
        t.resizable(False, False)
        t.mainloop()

    def chooseSensorsDialogue(self, names, filename):
        t = Toplevel(self)
        t.title("Sensors")
        paddingFrame = Frame(t)
        paddingFrame.pack(fill=BOTH, expand=True, padx=8, pady=8)
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

        t.grab_set()
        self.wait_window(t)
        return [n.get() == 1 for n in self.checkboxVars]

    def renameDialog(self, iid):
        parent = self.master.importList.parent(iid)
        if parent:
            run = self.master.indexPointers[parent]
        else:
            run = self.master.indexPointers[iid]

        t = Toplevel(self)
        t.title("Rename")
        paddingFrame = Frame(t)
        paddingFrame.pack(side=TOP, fill=BOTH, expand=True, padx=8, pady=8)
        Label(paddingFrame, text="Run name:").grid(row=0, column=0)
        runEntry = Entry(paddingFrame)
        runEntry.insert(END, run["runname"])
        runEntry.grid(row=0, column=1, pady=(0,4))
        sensorList = run["sensors"].items()
        oldSensorNames = [name for name, _ in sensorList]
        sensorEntries = [Entry(paddingFrame) for _ in oldSensorNames]
        t.resizable(False, False)
        i = 0
        while i < len(sensorList):
            Label(paddingFrame, text="Sensor name:").grid(row=i+1, column=0, pady=(0,4))
            sensorEntries[i].insert(END, oldSensorNames[i])
            sensorEntries[i].grid(row=i+1, column=1, pady=(0,4))
            i += 1
        Button(paddingFrame, text="Cancel", command=t.destroy).grid(row=i+1, column=0)

        def doRename():
            runname = runEntry.get()
            if not runname:
                messagebox.showerror("Error", "Run name cannot be empty", parent=self)
                return

            forbiddenChars = "\/*[]:?()"
            if any(c in runname for c in forbiddenChars):
                messagebox.showerror("Error", "Cannot export runs into Excel with names containing '" + forbiddenChars + "'", parent=self)
                return

            sensornames = [se.get() for se in sensorEntries]
            for i in range(len(sensornames) - 1):
                for j in range(i+1, len(sensornames)):
                    if sensornames[i] == sensornames[j]:
                        messagebox.showerror("Error", "Sensor names must have distinct names.", parent=self)
                        return

            try:
                handle, tempPath = mkstemp()
                with open(tempPath, "w") as newfile:
                    newfile.write(runname + "\n")
                    with open(run["filename"], "r") as oldfile:
                        oldfile.readline() #throw away old name
                        line = oldfile.readline()
                        while line and line != "Sensor names:\n":
                            newfile.write(line)
                            line = oldfile.readline()
                        if not line:
                            messagebox.showerror("Error", "Unexpected end before sensor names", parent=self)
                            return
                        newfile.write(line)
                        line = oldfile.readline()
                        while line and line != "Initial thicknesses(mm) - Initial displacement:\n":
                            try:
                                index = oldSensorNames.index(line[:-1])
                                newfile.write(sensornames[index] + "\n")
                            except IndexError:
                                newfile.write(line)
                            line = oldfile.readline()
                        if not line:
                            messagebox.showerror("Error", "Unexpected end before data", parent=self)
                            return
                        newfile.write(line)
                        line = oldfile.readline()
                        while line:
                            newfile.write(line)
                            line = oldfile.readline()
                        oldfile.close()
                    newfile.close()
                shutil.move(tempPath, run["filename"])
                os.close(handle)
                t.destroy()
                messagebox.showinfo("Success", "Changes have been saved", parent=self)
            except:
                messagebox.showerror("Error", "Could not rename sensors.", parent=self)
                raise

        Button(paddingFrame, text="Save", command=doRename).grid(row=i+1, column=1, sticky=E)
        t.grab_set()
        self.wait_window(t)
        self.deleteObject(iid, warn=False)
        self.importRun(run["filename"])

    def importRun(self, filename):
        try:
            with open(filename, "r") as f:
                runname = f.readline()[:-1]

                f.readline()  # throw away human-readable date
                timeofrun = time.localtime(float(f.readline()[:-1]))

                if (runname, timeofrun) in self.loadedRuns:
                    res = messagebox.askyesno("Reload run", "Do you want to reload '" + runname + "'?", parent=self)
                    if not res:
                        return None
                    else:
                        iid, _ = self.loadedRuns[(runname, timeofrun)]
                        self.deleteObject(iid, warn=False)
                f.readline()  # 'Notes:'
                notes = ""
                while True:  # notes are delimited by single backslash
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
                f.readline()  # Sensor names:
                sensors = [
                    {"name": f.readline()[:-1], "times": [], "pdisplacements": [], "voltages": [], "toshow": True}
                    for _ in range(numsensors)]
                f.readline()  # "Initial thicknesses(mm) - Initial displacements(mm):
                for i in range(numsensors):
                    thicc, _, displacement = f.readline().split()
                    sensors[i]["initialThickness"] = float(thicc)
                    sensors[i]["initialDisplacement"] = float(displacement)
                f.readline()  # 'Time(m) - Displacement(%) - Voltage(V)'
                f.readline()  # newline

                line = f.readline()
                while line:
                    data = line.split()
                    for i in range(0, numsensors):
                        index = i * 3
                        sensors[i]["times"].append(float(data[index]))
                        sensors[i]["pdisplacements"].append(float(data[index + 1]))
                        sensors[i]["voltages"].append(float(data[index + 2]))
                    line = f.readline()

                toimport = self.chooseSensorsDialogue([sensors[i]["name"] for i in range(numsensors)], filename)
                sensors = {sensors[i]["name"]: sensors[i] for i in range(numsensors) if toimport[i]}
                run = {"runname": runname, "timeofrun": timeofrun, "sensors": sensors, "notes": notes,
                             "toshow": True, "filename": filename}
                f.close()
                return run
        except Exception as e:
            messagebox.showerror("Error", "Could not import data from '" + os.path.basename(filename) + "'.",
                                 parent=self)
            raise e

    def importData(self):
        filenames = filedialog.askopenfilenames(parent=self, defaultextension=".data",
                                                filetypes=[("Data File", "*.data")])
        if not filenames:
            return

        runs = [self.importRun(filename) for filename in filenames if not None]

        for run in runs:
            rootid = self.importList.insert("", "end",
                                            values=(str(len(self.loadedRuns) + 1) + " - " + run["runname"], True),
                                            open=True, tags=("run"))
            self.loadedRuns[(run["runname"], run["timeofrun"])] = [rootid, run]
            self.indexPointers[rootid] = run
            for name, sensor in run["sensors"].items():
                self.indexPointers[self.importList.insert(rootid, "end", values=(name, True))] = sensor

        self.setGraphMode()


if __name__ == "__main__":
    AnalysisWindow()

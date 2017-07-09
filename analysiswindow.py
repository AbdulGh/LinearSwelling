import time
import os
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter import font
from tkinter.ttk import *

class AnalysisWindow(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Swellometer")
        self.loadedRuns = []
        self.initwindow()
        self.resizable(False, False)

        self.style = Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

    def initwindow(self):
        mainFrame = Frame(self)
        mainFrame.pack(fill=BOTH, padx=8, pady=8)

        currentLoadedFrame = Frame(mainFrame)
        currentLoadedFrame.pack(side=LEFT)

        listFrame = Frame(currentLoadedFrame, width=300)
        listFrame.pack(side=TOP)
        scrollbar = Scrollbar(listFrame)
        importList = Treeview(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED, columns=("name", "points"))
        scrollbar.config(command=importList.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        importList["show"] = "headings"
        importList.heading("name", text="Name")
        importList.column("name", minwidth=100, width=200)
        importList.heading("points", text="# points")
        importList.column("points", minwidth=10, width=100)
        importList.pack(side=LEFT, fill=BOTH, expand=True)

        self.indexPointers = {} #points to which object to display on double click
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

        Button(currentLoadedFrame, text="Import...", command=self.importData).pack(side=RIGHT, pady=(4,0))

        self.mainloop()

    def deleteObject(self, id):
        pointed = self.indexPointers[id]
        if "runname" in pointed:
            res = messagebox.askyesno("Delete run", "Are you sure you want to delete this run and all of its data?")
            if res == "no":
                return
            else:
                for i in self.importList.get_children(id):
                    del self.indexPointers[i]
                    self.importList.delete(i)
        self.importList.delete(id)
        del self.indexPointers[id]

    def runInfoDialog(self, run):
        t = Toplevel(self)

        t.style = Style()
        if "clam" in t.style.theme_names():
            t.style.theme_use("clam")

        frame = Frame(t)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        Label(frame, text="Name: " + run["runname"]).pack(side=TOP)
        Label(frame, text="Time: " + time.strftime("%a, %d %b %Y %H:%M:%S", run["timeofrun"])).pack(side=TOP)

        listbox = Listbox(frame, height=0)

        for name, sensor in run["sensors"].items():
            listbox.insert(END, name)

        def listDoubleClick(_):
            pointed = run["sensors"][listbox.selection_get()]
            self.sensorInfoDialog(pointed)

        listbox.pack(side=TOP, fill=X, expand=True)
        listbox.bind("<Double-1>", listDoubleClick)

        Button(frame, text="OK", command=t.destroy).pack(side=RIGHT, pady=(4,0))
        t.resizable(False, False)
        t.mainloop()

    def sensorInfoDialog(self, sensor):
        t = Toplevel(self)

        t.style = Style()
        if "clam" in t.style.theme_names():
            t.style.theme_use("clam")

        frame = Frame(t)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        Label(frame, text="Name: " + sensor["name"]).pack(side=TOP)
        Label(frame, text="# of readings: " + str(len(sensor["times"]))).pack(side=TOP)

        listFrame = Frame(frame, width=300)
        listFrame.pack(side=TOP)
        scrollbar = Scrollbar(listFrame)
        resList = Treeview(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED, columns=("time", "distance", "voltage"))
        scrollbar.config(command=resList.yview)
        resList["show"] = "headings"
        resList.heading("time", text="Time (s)")
        resList.column("time", minwidth=10, width=100)
        resList.heading("distance", text="Distance (mm)")
        resList.column("distance", minwidth=10, width=100)
        resList.heading("voltage", text="Voltage (mV)")
        resList.column("voltage", minwidth=10, width=100)

        for i in range(len(sensor["times"])):
            resList.insert("", "end", i, values=(sensor["times"][i], sensor["distances"][i], sensor["voltages"][i]))

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
        for n in range(len(names)):
            self.checkboxVars[n].set(1)
            Checkbutton(paddingFrame, text=names[n], variable=self.checkboxVars[n]).pack(side=TOP, pady=4)

        t.resizable(False, False)
        Button(paddingFrame, text="Import", command=t.destroy).pack(side=TOP)

        self.wait_window(t)

        return [n.get() == 1 for n in self.checkboxVars]

    def importData(self):
        filenames = filedialog.askopenfilenames()
        if not filenames:
            return

        runs = []
        for filename in filenames:
            try:
                with open(filename, "r") as f:
                    runname = f.readline()
                    f.readline() #throw away human-readable date
                    timeofrun = time.localtime(float(f.readline()[:-2]))
                    rate = f.readline().split()[1]
                    f.readline()
                    f.readline()
                    names = []
                    sensors = []
                    line = f.readline()
                    while line != "" and line != "\n":
                        line = line.split()
                        if len(line) < 3 or line[0] != "***":
                            raise IOError("Invalid file")
                        sensor = {}
                        name = " ".join(line[1:-1])
                        names.append(name)
                        calib = f.readline().split()
                        sensor["params"] = [float(calib[5]), float(calib[8])]
                        sensor["name"] = name
                        sensor["times"] = []
                        sensor["distances"] = []
                        sensor["voltages"] = []
                        line = f.readline()
                        while line != "" and line != "\n":
                            ar = line.split()
                            if len(ar) != 3:
                                raise IOError("Invalid file")
                            sensor["times"].append(float(ar[0]))
                            sensor["distances"].append(float(ar[1]))
                            sensor["voltages"].append(float(ar[2]))
                            line = f.readline()
                        sensors.append(sensor)
                        line = f.readline()

                    if len(names) == 0:
                        raise IOError("Invalid file")

                    toimport = self.chooseSensorsDialogue(names, filename)
                    sensors = {names[i]:sensors[i] for i in range(len(names)) if toimport[i]}
                    runs.append({"runname": runname, "timeofrun": timeofrun, "rate":rate, "sensors": sensors})
            except:
                messagebox.showerror("Error", "Could not import data from '" + os.path.basename(filename) + "'.")
        for run in runs:
            if run not in self.loadedRuns: #todo deal w/ loading the same run multiple times w/ different sensors
                rootid = self.importList.insert("", "end", values=(run["runname"], ""), open=True, tags=("run"))
                self.indexPointers[rootid] = run
                for name, sensor in run["sensors"].items():
                    self.indexPointers[self.importList.insert(rootid, "end", values=(name, str(len(sensor["times"]))))] = sensor
                self.loadedRuns.append(run)

def test():
    a = AnalysisWindow()
    
if __name__ == "__main__":
    test()

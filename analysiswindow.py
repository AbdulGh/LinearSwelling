import time
from tkinter import *
from tkinter.ttk import *

class RunObject(): #todo load sensors into 4 things
    def __init__(self, filename):
        with open(filename, "r") as f:
            self.name = f.readline()
            self.time = time.localtime(float(f.readline()[:-2]))
            self.rate = f.readline().split()[1]
            f.readline()
            f.readline()
            self.voltages = []
            self.distances = []
            self.times = []
            self.params = []
            while f.readline()[0:3] == "***":
                calib = f.readline().split()
                self.params.append([float(calib[5]), float(calib[8][:2])])
                t = []
                v = []
                d = []
                line = f.readline()
                while line and line != "\n":
                    ar = line.split()
                    if len(ar) != 3:
                        raise "Invalid file"
                    t.append(float(ar[0]))
                    d.append(float(ar[1]))
                    v.append(float(ar[2]))
                    line = f.readline()
                self.voltages.append(v)
                self.distances.append(d)
                self.times.append(t)

    def infoDialog(self, master=None):
        t = Toplevel(master)

        t.style = Style()
        if "clam" in t.style.theme_names():
            t.style.theme_use("clam")

        frame = Frame(t)
        frame.pack(fill=BOTH, expand=True, padx=8, pady=8)
        Label(frame, text="Name: " + self.name).pack(side=TOP)
        Label(frame, text="Time: " + time.strftime("%a, %d %b %Y %H:%M:%S", self.time)).pack(side=TOP)
        Label(frame, text="# sensors: " + str(len(self.distances))).pack(side=TOP)
        Label(frame, text="# of readings: " + str(len(self.distances[0]))).pack(side=TOP)

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

        for i in range(len(self.distances)):
            id = resList.insert("", "end", i, values=(">Sensor" + str(i + 1)))
            resList.item(id, open=True)
            for j in range(len(self.distances[i])):
                resList.insert(id, "end", values=(round(self.times[i][j],3), round(self.distances[i][j],3), round(self.voltages[i][j],3)))

        resList.pack(side=LEFT, fill=BOTH, expand=True, pady=4)
        scrollbar.config(command=resList.yview)
        scrollbar.pack(side=RIGHT, fill=Y, pady=4)

        Button(frame, text="OK", command=t.destroy).pack(side=RIGHT)
        t.resizable(False, False)
        t.mainloop()

class AnalysisWindow(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Swellometer")
        self.minsize(200, 200)
        self.resizable(False, False)

        self.initwindow()

        self.style = Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.loadedROs = []

        self.mainloop()

    def initwindow(self):
        listFrame = Frame(self)
        scrollbar = Scrollbar(listFrame)
        scrollbar.pack(side=RIGHT, fill=Y)
        list = Listbox(listFrame, selectmode=EXTENDED, yscrollcommand=scrollbar.set)
        list.pack(side=LEFT, fill=BOTH, expand=True)

if __name__ == "__main__":
    RunObject("export").infoDialog(None)



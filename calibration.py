from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *
import scipy.stats
import random
import tools
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class CalibrationWindow(Toplevel):

    def __init__(self, master=None):
        Toplevel.__init__(self, master)
        self.title("Swellometer calibration")
        self.resizable(False, False)

        self.readoutAfterID = None
        self.measurementAfterID = None
        self.xs = []
        self.ys = []
        self.results = []

        """
        if not self.initial_focus:
            self.initial_focus = self

        self.initial_focus.focus_set()
        """

        self.protocol("WM_DELETE_WINDOW", self.fin)

        self.initwindow()

        self.wait_window(self)

    def initwindow(self):
        #self.pack(fill=BOTH, expand=True, padx=6, pady=6)

        mainFrame = Frame(self)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True)

        leftFrame = Frame(mainFrame)
        leftFrame.pack(side=TOP, fill=BOTH, expand=True)

        inputFrame = Frame(leftFrame)
        inputFrame.grid(row=0, column=0, rowspan=3, columnspan=3)
        vernL = Label(inputFrame, text="Distance (mm): ", width=20)
        vernL.grid(row=0, column=0, padx=5, pady=5)
        vernEntry = Entry(inputFrame)
        vernEntry.cname = "Distance"
        vernEntry.grid(row=0, column=1, padx=5)
        self.vernEntry = vernEntry

        readingsL = Label(inputFrame, text="Total # of readings: ", width=20)
        readingsL.grid(row=1, column=0, padx=5, pady=5)
        readingsEntry = Entry(inputFrame)
        readingsEntry.insert(0, "20")
        readingsEntry.cname = "Total # of readings"
        readingsEntry.grid(row=1, column=1, padx=5)
        self.readingsEntry = readingsEntry

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

        cancelBtn = Button(measurementFrame, text="Cancel", command=self.stopReadings)
        cancelBtn.grid(row=0, column=0, padx=2)
        cancelBtn.config(state=DISABLED)
        self.cancelBtn = cancelBtn
        startBtn = Button(measurementFrame, text="Start", command=self.startReadings)
        startBtn.grid(row=0, column=1, padx=2)
        self.startBtn = startBtn

        curReading = Label(measurementFrame)
        self.currentReadingUpdate(curReading)
        curReading.grid(row=2, column=0, columnspan=2)

        curMean = Label(measurementFrame, text="Current mean: -- V")
        curMean.grid(row=3, column=0, columnspan=2)
        self.curMean = curMean

        curNumTaken = Label(measurementFrame, text="Readings taken: 0")
        curNumTaken.grid(row=4, column=0, columnspan=2)
        self.curNumTaken = curNumTaken

        listFrame = Frame(leftFrame)
        scrollbar = Scrollbar(listFrame)
        resList = Listbox(listFrame, yscrollcommand=scrollbar.set, selectmode=EXTENDED)
        resList.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=resList.yview)

        def deleteSelected():
            nonlocal resList
            items = map(int, resList.curselection())
            print(items)

        menu = Menu(listFrame, tearoff=0)
        menu.add_command(label="Delete", command=deleteSelected)

        def popup(event):
            print("hi")
            menu.post(event.x_root, event.y_root)

        listFrame.bind("<Button-3>", popup)
        listFrame.grid(row=7, rowspan=9, column=0, columnspan=3, padx=6, sticky=N+S+W+E)

        scrollbar.pack(side=RIGHT, fill=Y)
        self.resList = resList

        graph = self.initGraphFrame(leftFrame) #todo see what happens when this is put in the right place
        graph.grid(row=0, column=3, rowspan=15, columnspan=4)

        bottomBtnFrame = Frame(self)
        bottomBtnFrame.pack(side=BOTTOM, fill=X)
        exitBtn = Button(bottomBtnFrame, text="Done", command=self.fin)
        exitBtn.pack(side=RIGHT, padx=5, pady=5)

    class CalibrationResult:
        def __init__(self, dist, inductionList):
            self.dist = dist
            self.num = len(inductionList)
            self.inductionList = inductionList
            self.mean = sum(inductionList) / len(inductionList)
            self.SD = scipy.std(inductionList)

        def toStr(self):
            return str(self.dist) + "mm    -    " + str(round(self.mean,3)) + "V    -    SD " + str(round(self.SD, 3)) + "V"

    def startReadings(self):
        distance = tools.getFloatFromEntry(self.vernEntry, mini=0.1)
        rate = tools.getFloatFromEntry(self.rateEntry, mini=0)
        totalNo = tools.getFloatFromEntry(self.readingsEntry, mini=1, forceInt=True)

        if (distance is None or rate is None or totalNo is None):
            return

        rate = int(1000/rate)
        totalNo = int(totalNo)

        self.cancelBtn.config(state=NORMAL)
        self.startBtn.config(state=DISABLED)

        currentReadings = []
        tot = 0
        self.curMean.config(text="Current mean: " + str(tot) + " V")
        self.curNumTaken.config(text="Readings taken: 0/" + str(totalNo))

        def addResults():
            res = tot/len(currentReadings)

            self.xs.append(distance)
            self.ys.append(res)
            cr = self.CalibrationResult(distance, currentReadings)
            self.results.append(cr)

            if distance > self.maxX:
                self.maxX = distance + 1
            if res > self.maxY:
                self.maxY = res + 1

            self.graph.clear()
            self.graph.scatter(self.xs, self.ys)
            self.graph.set_xlim([0, self.maxX])
            self.graph.set_ylim([0, self.maxY])

            if checkDifferent(self.xs):
                m, b, r_value, _, _ = scipy.stats.linregress(self.xs, self.ys)
                self.graph.set_title("y = " + str(m) + "x + " + str(b) + "           r = " + str(r_value))
                self.graph.plot([0, self.maxX], [b, m * self.maxX + b], '-', color="red")

            self.graph.set_xlabel("Distance (mm)")
            self.graph.set_ylabel("Inductance (V)")

            self.canvas.draw()
            self.stopReadings()

            self.resList.insert(END, cr.toStr())

        def takeSingleResult():
            nonlocal tot

            if len(currentReadings) == totalNo:
                addResults()
                self.stopReadings()
                return

            i = tools.getCurrentReading()
            tot += i
            currentReadings.append(i)
            self.curMean.config(text="Current mean: " + str(round(tot/len(currentReadings), 2)) + " V")
            self.curNumTaken.config(text="Readings taken: " + str(len(currentReadings)) + "/" + str(totalNo))

            self.measurementAfterID = self.measurementFrame.after(rate, takeSingleResult)

        takeSingleResult()

    def stopReadings(self):
        self.cancelBtn.config(state=DISABLED)
        self.startBtn.config(state=NORMAL)

        if self.measurementAfterID is not None:
            self.measurementFrame.after_cancel(self.measurementAfterID)
            self.measurementAfterID = None

        self.curMean.config(text="Current mean: -- V")
        self.curNumTaken.config(text="Readings taken: 0")

    def initGraphFrame(self, fr):
        f = Figure(figsize=(8, 5), dpi=100)
        a = f.add_subplot(111)
        a.set_xlabel("Distance (mm)")
        a.set_ylabel("Inductance (V)")
        self.maxX = self.maxY = 10
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

    def currentReadingUpdate(self, label):
        update = int(1000 / tools.getFloatFromEntry(self.rateEntry, mini=0))
        def readingUpdate():
            i = tools.getCurrentReading()
            label.config(text="Current reading(mv): " + str(i))
            self.readoutAfterID = label.after(update, readingUpdate)
        if self.readoutAfterID is not None:
            label.after_cancel(self.readoutAfterID)
        readingUpdate()

    def fin(self):
        if (len(self.xs) < 2):
            result = messagebox.askquestion("Not enough points", "Cancel calibration?", icon='warning')
            if result == "yes":
                self.master.destroy()
        else:
            done = False
            while not done:
                result = messagebox.askquestion("Save", "Save settings?")
                if result == "yes":
                    f = filedialog.asksaveasfile(mode='w')
                    if f is not None:
                        m, b = self.getsettings()
                        f.write(str(m) + '\n' + str(b))
                        f.close()
                        self.master.destroy()
                        done = True
                else:
                    self.master.destroy()
                    done = True

    def getsettings(self):
        if (len(self.xs) > 1):
            m, b, _, _, _ = scipy.stats.linregress(self.xs, self.ys)
            return m,b

def checkDifferent(l):
    if len(l) < 2:
        return False
    x = l[0]
    for i in range(1, len(l)):
        if l[i] != x:
            return True
    return False

"""
if __name__ == '__main__':
    #root = Tk()
    calibrationWindow = CalibrationWindow()
    #root.mainloop()
"""
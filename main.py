from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
import scipy.stats
import random

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class CalibrationWindow(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.master = master
        self.master.minsize(1100,550)
        self.master.geometry("1100x550")
        self.master.resizable(False, False)

        self.readoutAfterID = None
        self.measurementAfterID=None
        self.xs = []
        self.ys = []
        self.stdDevs = []

        self.initwindow()

    def initwindow(self):
        self.master.title("Calibration")
        self.pack(fill=BOTH, expand=True, padx=6, pady=6)

        mainFrame = Frame(self)
        mainFrame.pack(side=TOP, fill=BOTH, expand=True)

        leftFrame = Frame(mainFrame)
        leftFrame.pack(side=TOP, fill=BOTH, expand=True)

        inputFrame = Frame(leftFrame)
        inputFrame.grid(row=0, column=0, rowspan=3, columnspan=3)
        vernL = Label(inputFrame, text="Measured distance (mm): ", width=20)
        vernL.grid(row=0, column=0, padx=5, pady=5)
        vernEntry = Entry(inputFrame)
        vernEntry.cname = "Measured distance"
        vernEntry.grid(row=0, column=1, padx=5)
        self.vernEntry = vernEntry

        readingsL = Label(inputFrame, text="Total # of readings: ", width=20)
        readingsL.grid(row=1, column=0, padx=5, pady=5)
        readingsEntry = Entry(inputFrame)
        readingsEntry.insert(0, "20")
        readingsEntry.cname = "Total # of readings"
        readingsEntry.grid(row=1, column=1, padx=5)
        self.readingsEntry = readingsEntry

        rateL = Label(inputFrame, text="Readings/second:", width=20)
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
        cancelBtn.grid(row=0, column=0)
        cancelBtn.config(state=DISABLED)
        self.cancelBtn = cancelBtn
        startBtn = Button(measurementFrame, text="Start", command=self.startReadings)
        startBtn.grid(row=0, column=1)
        self.startBtn = startBtn

        curReading = Label(measurementFrame)
        self.currentReadingUpdate(curReading)
        curReading.grid(row=2, column=0, columnspan=2)

        curMean = Label(measurementFrame, text="Current mean: -- V", width=30)
        curMean.grid(row=3, column=0, columnspan=2)
        self.curMean = curMean

        curNumTaken = Label(measurementFrame, text="Readings taken: 0")
        curNumTaken.grid(row=4, column=0, columnspan=2)
        self.curNumTaken = curNumTaken

        listFrame = Frame(leftFrame, bd=1, relief=SUNKEN)
        listFrame.grid(row=7, rowspan=9, column=0, columnspan=3, padx=6, sticky=N+S+W+E)
        scrollbar = Scrollbar(listFrame)
        resList = Listbox(listFrame, yscrollcommand=scrollbar.set)
        resList.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=resList.yview)

        scrollbar.pack(side=RIGHT, fill=Y)
        self.resList = resList

        graph = self.initGraphFrame(leftFrame)
        graph.grid(row=0, column=3, rowspan=15, columnspan=5)

        bottomBtnFrame = Frame(self)
        bottomBtnFrame.pack(side=BOTTOM, fill=X)
        exitBtn = Button(bottomBtnFrame, text="Done", command=self.fin)
        exitBtn.pack(side=RIGHT, padx=5, pady=5)

    def getFloatFromEntry(self, entry, mini=None, maxi=None, forceInt=False):
        s = entry.get()
        try:
            i = float(s)
            if (mini is not None and i < mini):
                messagebox.showerror("Error", "Value for '" + entry.cname + "' is too small (minimum " + str(mini) + ")")
            elif (maxi is not None and i > maxi):
                messagebox.showerror("Error", "Value for '" + entry.cname + "' is too large (maximum " + str(maxi) + ")")
            elif forceInt and not i.is_integer():
                messagebox.showerror("Error", "Value for '" + entry.cname + "' must be an integer")
            else:
                return i
        except ValueError:
            messagebox.showerror("Error", "Value for '" + entry.cname + "' is not numerical")

    def getCurrentReading(self):
        return random.randint(0, 10)

    def startReadings(self):
        distance = self.getFloatFromEntry(self.vernEntry, mini=0)
        rate = self.getFloatFromEntry(self.rateEntry, mini=0)
        totalNo = self.getFloatFromEntry(self.readingsEntry, mini=1, forceInt=True)

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
            SD = scipy.std(currentReadings)
            self.stdDevs.append(SD)

            if distance > self.maxX:
                self.maxX = distance + 1
            if res > self.maxY:
                self.maxY = res + 1

            self.graph.clear()
            self.graph.scatter(self.xs, self.ys)
            self.graph.set_xlim([0, self.maxX])
            self.graph.set_ylim([0, self.maxY])

            if len(self.xs) >= 2:
                m, b, r_value, _, _ = scipy.stats.linregress(self.xs, self.ys)
                self.graph.set_title("y = " + str(m) + "x + " + str(b) + "           r = " + str(r_value))
                self.graph.plot([0, self.maxX], [b, m * self.maxX + b], '-', color="red")

            self.graph.set_xlabel("Distance (mm)")
            self.graph.set_ylabel("Inductance (V)")

            self.canvas.draw()
            self.stopReadings()

            self.resList.insert(END, str(distance) + "mm    -    " + str(res) + "V    -    SD " + str(SD) + "V")

        def takeSingleResult():
            nonlocal tot

            if len(currentReadings) == totalNo:
                addResults()
                self.stopReadings()
                return

            i = self.getCurrentReading()
            tot += i
            currentReadings.append(i)
            self.curMean.config(text="Current mean: " + str(tot/len(currentReadings)) + " V")
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

        wrapper = Frame(fr, bd=1, relief=SUNKEN)
        canvas = FigureCanvasTkAgg(f, wrapper)
        canvas.show()
        self.canvas = canvas

        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        return wrapper

    def currentReadingUpdate(self, label):
        update = int(1000 / self.getFloatFromEntry(self.rateEntry))
        def readingUpdate():
            i = self.getCurrentReading()
            label.config(text="Current reading(mv): " + str(i))
            self.readoutAfterID = label.after(update, readingUpdate)
        if self.readoutAfterID is not None:
            label.after_cancel(self.readoutAfterID)
        readingUpdate()

    def fin(self):
        if (len(self.xs) < 2):
            result = messagebox.askquestion("Not enough points", "Cancel calibration?", icon='warning')
            if result == "yes":
                exit()
        else:
            done = False
            while not done:
                result = messagebox.askquestion("Save", "Save settings?")
                if result == "yes":
                    f = filedialog.asksaveasfile(mode='w')
                    if f is not None:
                        f.write(self.getsettings())
                        f.close()
                        done = True
                else:
                    done = True

    def getsettings(self):
        if (len(self.xs) > 1):
            return scipy.stats.linregress(self.xs, self.ys)


if __name__ == '__main__':
    root = Tk()
    calibrationWindow = CalibrationWindow(root)
    root.mainloop()

from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import numpy as np
from math import floor

class AnalysisGraph(Frame):
    def __init__(self, master): #master must be an AnalysisWindow
        Frame.__init__(self, master, relief=SUNKEN, borderwidth=1)
        self.master = master
        self.tofilter = False
        self.autoscaleX = self.autoscaleY = True
        f = Figure(figsize=(8, 5), dpi=100)
        a = f.add_subplot(111)
        self.graph = a

        canvas = FigureCanvasTkAgg(f, self)
        self.canvas = canvas
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        def savelims():
            self.xmin, self.xmax = self.graph.get_xlim()
            self.ymin, self.ymax = self.graph.get_ylim()

        class NavigationToolbar(NavigationToolbar2TkAgg): 
            def __init__(self, canvas, parent): #get rid of subplot stuff
                self.toolitems = [t for t in NavigationToolbar2TkAgg.toolitems if t[0] in ("Home", "Pan", "Zoom", "Save")]
                NavigationToolbar2TkAgg.__init__(self, canvas, parent)
                self.parent = parent

            def press_pan(self, event): #save lims after zoom/pan
                NavigationToolbar2TkAgg.press_pan(self, event)
                savelims()
                self.parent.autoscaleX = self.parent.autoscaleY = False

            def press_zoom(self, event):
                NavigationToolbar2TkAgg.press_zoom(self, event)
                savelims()
                self.parent.autoscaleX = self.parent.autoscaleY = False

        self.toolbar = NavigationToolbar(canvas, self)
        self.toolbar.update()
        canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=True)
        savelims()
        self.graph.set_autoscale_on(False)

    def clear(self):
        self.graph.clear()

    """
    def setLims(self, xmin=None, xmax=None, ymin=None, ymax=None):
        if xmin is not None:
            self.xmin = xmin
        if xmax is not None:
            self.xmax = xmax
        if ymin is not None:
            self.ymin = ymin
        if ymax is not None:
            self.ymax = ymax
        self.scaleToLims()
    """

    """Returns [xmin, xmax, ymin, ymax]"""
    def getCurrentLims(self):
        return self.graph.get_xlim() + self.graph.get_ylim()

    def meanFilter(self, ys, n=7):
        length = min(len(ys), n)
        if length % 2 != 0:
            length += 1
        mask = np.ones(length)/length
        valid = list(np.convolve(ys, mask, mode="valid"))
        missed = floor(length/2)
        return np.concatenate((ys[:missed], valid, ys[-missed + 1:]))

    def plotDistances(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Displacement (%)")

        for i in range(len(runs)):
            run = runs[i]
            if not run["toshow"]:
                continue


            prefix = str(i+1) + " - " if len(runs) > 1 else ""
            if self.tofilter:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    self.graph.plot(sensor["times"], self.meanFilter(sensor["pdisplacements"]), label=prefix + sensorname)
            else:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    self.graph.plot(sensor["times"], sensor["pdisplacements"], label=prefix + sensorname)
        self.updateGraph()

    def plotAverageDistance(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Average swell (%)")

        #get number of readings

        for run in runs:
            if not run["toshow"]:
                continue

            numvalues = len(next(iter(run["sensors"].values()))["pdisplacements"])
            numsensors = len(run["sensors"])

            sumDisplacements = np.zeros(numvalues)
            sumTimes = np.zeros(numvalues)
            for _, sensor in run["sensors"].items():
                if not sensor["toshow"]:
                    continue
                sumDisplacements += np.array(sensor["pdisplacements"])
                sumTimes += np.array(sensor["times"])
            sumDisplacements /= numsensors
            sumTimes /= numsensors

            if self.tofilter:
                sumDisplacements = self.meanFilter(sumDisplacements)

            self.graph.plot(sumTimes, sumDisplacements, label=run["runname"])

        self.updateGraph()

    def plotVoltages(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Voltage (V)")

        for i in range(len(runs)):
            if not runs[i]["toshow"]:
                continue

            run = runs[i]
            prefix = str(i + 1) + " - " if len(runs) > 1 else ""
            if self.tofilter:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    self.graph.plot(sensor["times"], self.meanFilter(sensor["voltages"]), label=prefix + sensorname)
            else:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    self.graph.plot(sensor["times"], sensor["voltages"], label=prefix + sensorname)
        self.updateGraph()

    def plotTotalSwells(self, runs):
        self.clear()
        self.graph.set_ylabel("Total swell (%)")

        xtics = []
        totalSwells = []
        for i in range(len(runs)):
            if not runs[i]["toshow"]:
                continue

            run = runs[i]
            prefix = str(i + 1) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
                if not sensor["toshow"]:
                    continue

                xtics.append(prefix + sensorname)
                totalSwells.append(sensor["pdisplacements"][-1])
        if len(totalSwells) == 0:
            return

        indexes = np.arange(len(xtics))
        self.graph.bar(indexes, totalSwells, align="center")
        self.graph.set_xticks(indexes)
        self.graph.set_xticklabels(xtics, rotation=20, ha="right")
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

    def plotRatePercentageSwell(self, runs):
        self.clear()
        self.graph.set_ylabel("Rate of swelling (%/m)")
        self.graph.set_xlabel("Time (m)")

        if len(runs) == 0:
            self.updateGraph()
            return

        for i in range(len(runs)):
            run = runs[i]
            if not run["toshow"]:
                continue

            prefix = str(i + 1) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
                displacements = sensor["pdisplacements"]
                times = sensor["times"]

                if len(times) <= 1:
                    continue

                xs = []
                ys = []
                lastDisplacement = displacements[0]
                lastTime = times[0]
                for i in range(1, len(times)):
                    if displacements[i] > lastDisplacement:
                        xs.append((times[i] - lastTime)/2)
                        ys.append((displacements[i] - lastDisplacement) / (times[i] - lastTime))
                        lastDisplacement = displacements[i]
                        lastTime = times[i]

                self.graph.plot(xs, ys, label=prefix + sensorname)

    def plotAverageSwellingRate(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Average rate (%/m)")

        #get number of readings

        for run in runs:
            if not run["toshow"]:
                continue

            numvalues = len(next(iter(run["sensors"].values()))["pdisplacements"])
            numsensors = len(run["sensors"])

            sumDisplacements = np.zeros(numvalues)
            sumTimes = np.zeros(numvalues)
            for _, sensor in run["sensors"].items():
                if not sensor["toshow"]:
                    continue

                sumDisplacements += np.array(sensor["pdisplacements"])
                sumTimes += np.array(sensor["times"])
            sumDisplacements /= numsensors
            sumTimes /= numsensors

            if self.tofilter:
                sumDisplacements = self.meanFilter(sumDisplacements)

            self.graph.plot(sumTimes, sumDisplacements, label=run["runname"])
        self.updateGraph()

    def scaleToLims(self):
        self.graph.relim()
        self.graph.autoscale_view(scalex=self.autoscaleX, scaley=self.autoscaleY)
        if not self.autoscaleX:
            self.graph.set_xlim([self.xmin, self.xmax])
        else:
            self.xmin, self.xmax = self.graph.get_xlim()
        if not self.autoscaleY:
            self.graph.set_ylim([self.ymin, self.ymax])
        else:
            self.ymin, self.ymax = self.graph.get_ylim()

    def updateGraph(self):
        self.scaleToLims()
        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.canvas.draw()
        self.toolbar.update()

if __name__ == '__main__':
    print("Run main.py")


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
        self.lastx = self.lasty = None
        f = Figure(figsize=(8, 5), dpi=100)
        a = f.add_subplot(111)
        self.graph = a

        canvas = FigureCanvasTkAgg(f, self)
        self.canvas = canvas
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        class NavigationToolbar(NavigationToolbar2TkAgg): 
            def __init__(self, canvas, parent): #get rid of subplot stuff
                self.toolitems = [t for t in NavigationToolbar2TkAgg.toolitems if t[0] in ("Home", "Pan", "Zoom", "Save")]
                NavigationToolbar2TkAgg.__init__(self, canvas, parent)

        self.toolbar = NavigationToolbar(canvas, self)
        self.toolbar.update()
        canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=True)

    def clear(self):
        self.graph.clear() 

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

        if len(runs) == 0:
            self.canvas.draw()
            return

        for i in range(len(runs)):
            run = runs[i]
            prefix = str(i+1) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
                if self.tofilter:
                    self.graph.plot(sensor["times"], self.meanFilter(sensor["pdisplacements"]), label=prefix + sensorname)
                else:
                    self.graph.plot(sensor["times"], sensor["pdisplacements"], label=prefix + sensorname)
        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

    def plotAverageDistance(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Average swell (%)")

        #get number of readings
        if len(runs) == 0:
            self.canvas.draw()
            return

        for run in runs:
            numvalues = len(next(iter(run["sensors"].values()))["pdisplacements"])
            numsensors = len(run["sensors"])

            sumDisplacements = np.zeros(numvalues)
            sumTimes = np.zeros(numvalues)
            for _, sensor in run["sensors"].items():
                sumDisplacements += np.array(sensor["pdisplacements"])
                sumTimes += np.array(sensor["times"])
            sumDisplacements /= numsensors
            sumTimes /= numsensors

            if self.tofilter:
                sumDisplacements = self.meanFilter(sumDisplacements)

            self.graph.plot(sumTimes, sumDisplacements, label=run["runname"])

        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

    def plotVoltages(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Voltage (mV)")

        if len(runs) == 0:
            self.canvas.draw()
            return

        for i in range(len(runs)):
            run = runs[i]
            prefix = str(i + 1) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
                if self.tofilter:
                    self.graph.plot(sensor["times"], self.meanFilter(sensor["voltages"]), label=prefix + sensorname)
                else:
                    self.graph.plot(sensor["times"], sensor["voltages"], label=prefix + sensorname)
        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

    def plotTotalSwells(self, runs):
        self.clear()
        self.graph.set_ylabel("Total swell (%)")

        xtics = []
        totalSwells = []
        for i in range(len(runs)):
            run = runs[i]
            prefix = str(i + 1) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
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
            self.canvas.draw()
            return

        for i in range(len(runs)):
            run = runs[i]
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
                        lastTimes = times[i]

                self.graph.plot(xs, ys, label=prefix + sensorname)
        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()



    # def plotRatePercentageSwell(self, runs):
    #     self.clear()
    #     self.graph.set_ylabel("Rate of swelling (%/m)")
    #     self.graph.set_xlabel("Time (m)")

    #     if len(runs) == 0:
    #         self.canvas.draw()
    #         return

    #     for i in range(len(runs)):
    #         run = runs[i]
    #         prefix = str(i + 1) + " - " if len(runs) > 1 else ""
    #         for sensorname, sensor in run["sensors"].items():
    #             displacements = sensor["pdisplacements"]
    #             times = sensor["times"]

    #             if len(times) <= 1:
    #                 continue

    #             xs = []
    #             ys = []
    #             #we add the rate if the time exceeds 0.3 minutes or the relative displacement raises by 2%
    #             lastTime = times[0]
    #             lastDisplacement = displacements[0]
    #             for i in range(1, len(times)):
    #                 if times[i] - lastTime > 0.3 or displacements[i] - lastDisplacement > 2:
    #                     deltat = (times[i] - lastTime)
    #                     xs.append(lastTime + deltat/2)
    #                     ys.append((displacements[i] - lastDisplacement)/deltat)
    #                     lastTime = times[i]
    #                     lastDisplacement = displacements[i]
    #             self.graph.plot(xs, ys, label=prefix + sensorname)

    #     h, l = self.graph.get_legend_handles_labels()
    #     self.graph.legend(h, l)
    #     self.graph.autoscale(True)
    #     self.canvas.draw()
    #     self.toolbar.update()

    def plotAverageSwellingRate(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Average rate (%/m)")

        #get number of readings
        if len(runs) == 0:
            self.canvas.draw()
            return

        for run in runs:
            numvalues = len(next(iter(run["sensors"].values()))["pdisplacements"])
            numsensors = len(run["sensors"])

            sumDisplacements = np.zeros(numvalues)
            sumTimes = np.zeros(numvalues)
            for _, sensor in run["sensors"].items():
                sumDisplacements += np.array(sensor["pdisplacements"])
                sumTimes += np.array(sensor["times"])
            sumDisplacements /= numsensors
            sumTimes /= numsensors

            if self.tofilter:
                sumDisplacements = self.meanFilter(sumDisplacements)

            self.graph.plot(sumTimes, sumDisplacements, label=run["runname"])

        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

if __name__ == '__main__':
    print("Run main.py")


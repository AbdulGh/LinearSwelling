from tkinter import *

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import numpy as np
from math import floor
import scipy.optimize
from scipy.interpolate import interp1d
from scipy.signal import kaiserord, lfilter, firwin



class AnalysisGraph(Frame):
    def __init__(self, master):  # master must be an AnalysisWindow
        Frame.__init__(self, master, relief=SUNKEN, borderwidth=1)
        self.master = master
        self.tofilter = False
        self.autoscaleX = self.autoscaleY = True
        self.fig = Figure(figsize=(8, 5), dpi=100)
        a = self.fig.add_subplot(111)
        self.graph = a

        canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas = canvas
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        def savelims():
            self.xmin, self.xmax = self.graph.get_xlim()
            self.ymin, self.ymax = self.graph.get_ylim()

        class NavigationToolbar(NavigationToolbar2TkAgg):
            def __init__(self, canvas, parent):  # get rid of subplot stuff
                self.toolitems = [t for t in NavigationToolbar2TkAgg.toolitems if
                                  t[0] in ("Home", "Pan", "Zoom", "Save")]
                NavigationToolbar2TkAgg.__init__(self, canvas, parent)
                self.parent = parent

            def press_pan(self, event):  # save lims after zoom/pan
                NavigationToolbar2TkAgg.press_pan(self, event)
                savelims()
                self.parent.autoscaleX = self.parent.autoscaleY = False

            def release_zoom(self, event):
                NavigationToolbar2TkAgg.release_zoom(self, event)
                savelims()
                self.parent.autoscaleX = self.parent.autoscaleY = False

        self.toolbar = NavigationToolbar(canvas, self)
        self.toolbar.update()
        canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=True)
        savelims()
        self.graph.set_autoscale_on(False)

    def clear(self):
        self.graph.clear()

    """Returns [xmin, xmax, ymin, ymax]"""

    def getCurrentLims(self):
        return self.graph.get_xlim() + self.graph.get_ylim()

    def FIRFilterNonUniform(self, x, y):
        averageDiff = np.mean(np.diff(x))
        gridX, step = np.linspace(x[0], x[-1], np.ceil(x[-1]/averageDiff), retstep=True)
        rate = 1/step
        gridY = interp1d(x,y)(gridX)

        nyq = rate/2
        taps = firwin(1000, cutoff=0.1/nyq, nyq=nyq)
        filteredY = lfilter(taps, 1.0, gridY)

        return gridX, filteredY


    def fitModel(self, runs, xmin, xmax):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Displacement (%)")

        if len(runs) == 0:
            self.canvas.draw()
            self.toolbar.update()
            return

        def MMMGEW(times, a, b):
            sigmaterms = np.zeros(len(times))
            btimes = -b * times
            for n in range(0, 100):
                lambdaterm = ((n + 0.5) * np.pi) ** 2
                sigmaterms += (1 / lambdaterm) * np.exp(lambdaterm * btimes)
            return a * (1 - 2 * sigmaterms)

        params = {}
        for run in runs:
            runname = run["runname"]
            times = []
            displacements = []
            sensors = [sensor for _, sensor in run["sensors"].items() if sensor["toshow"]]
            for sensor in sensors:
                times.append(sensor["times"])
                displacements.append(sensor["pdisplacements"])

            numsensors = len(sensors)
            times = self.getAverages(times, numsensors)
            displacements = self.getAverages(displacements, numsensors)

            startindex = 0
            while times[startindex] < xmin:
                startindex += 1
                if startindex >= len(times):
                    return  # no data to plot
            startindex = max(0, startindex - 1)

            endindex = startindex
            while times[endindex] < xmax and endindex < len(times):
                endindex += 1

            times = np.array(times[startindex:endindex]) / 60
            times -= times[0]
            displacements = displacements[startindex:endindex]
            if self.tofilter:
                times, displacements = self.FIRFilterNonUniform(times, displacements)
            self.graph.plot(times, displacements, label=runname + " - average")
            [a, b], _ = scipy.optimize.curve_fit(MMMGEW, times, displacements)
            params[runname] = [a, b]

            estimatedy = MMMGEW(times, a, b)
            self.graph.plot(times, estimatedy, label=runname + " - estimate")

        self.graph.autoscale(True)
        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.canvas.draw()
        self.toolbar.update()
        return params

    def plotDistances(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Displacement (%)")

        if len(runs) == 0:
            self.canvas.draw()
            self.toolbar.update()
            return

        for i in range(len(runs)):
            run = runs[i]
            if not run["toshow"]:
                continue

            prefix = str(i + 1) + " - " if len(runs) > 1 else ""
            if self.tofilter:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    x,y = self.FIRFilterNonUniform(sensor["times"], sensor["pdisplacements"])
                    self.graph.plot(x, y, label=prefix + sensorname)
            else:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    self.graph.plot(sensor["times"], sensor["pdisplacements"], label=prefix + sensorname)
        self.updateGraph()

    def getAverages(self, xss, numsensors):
        if len(xss) == 0 or len(xss[0]) == 0:
            return
        sumxss = np.zeros(len(xss[0]))
        for xs in xss:
            sumxss += np.array(xs)
        sumxss /= numsensors

        return sumxss

    def plotAverageDistance(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Average swell (%)")

        if len(runs) == 0:
            self.canvas.draw()
            self.toolbar.update()
            return

        # get number of readings
        for run in runs:
            if not run["toshow"]:
                continue

            toavgtimes = []
            toavgdisplacement = []
            sensors = [sensor for _, sensor in run["sensors"].items() if sensor["toshow"]]
            numsensors = len(sensors)
            for sensor in sensors:
                toavgdisplacement.append(sensor["pdisplacements"])
                toavgtimes.append(sensor["times"])

            avgT = self.getAverages(toavgtimes, numsensors)
            avgD = self.getAverages(toavgdisplacement, numsensors)
            if self.tofilter:
                avgT, avgD = self.FIRFilterNonUniform(avgT, avgD)

            self.graph.plot(avgT, avgD, label=run["runname"])

        self.updateGraph()

    def plotVoltages(self, runs):
        self.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Voltage (V)")

        if len(runs) == 0:
            self.canvas.draw()
            self.toolbar.update()
            return

        for i in range(len(runs)):
            if not runs[i]["toshow"]:
                continue

            run = runs[i]
            prefix = str(i + 1) + " - " if len(runs) > 1 else ""
            if self.tofilter:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    times, voltages = self.FIRFilterNonUniform(sensor["times"], sensor["voltages"])
                    self.graph.plot(times, voltages, label=prefix + sensorname)
            else:
                for sensorname, sensor in run["sensors"].items():
                    if not sensor["toshow"]:
                        continue
                    self.graph.plot(sensor["times"], sensor["voltages"], label=prefix + sensorname)
        self.updateGraph()

    def plotTotalSwells(self, runs):
        self.clear()
        self.graph.set_ylabel("Total swell (%)")

        if len(runs) == 0:
            self.canvas.draw()
            self.toolbar.update()
            return

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

    def getDiscreteDerative(self, times, inys):
        times, displacements = self.FIRFilterNonUniform(times, inys)
        xs = []
        ys = []
        lastDisplacement = displacements[0]
        lastTime = times[0]
        for j in range(1, len(times)):
            #if the displacement has increased or some time has passed
            if displacements[j] - lastDisplacement > 4 or times[j] - lastTime > 2:
                xs.append(lastTime + (times[j] - lastTime) / 2)
                ys.append((displacements[j] - lastDisplacement) / (times[j] - lastTime))
                lastDisplacement = displacements[j]
                lastTime = times[j]

        return xs, ys

    def plotRatePercentageSwell(self, runs):
        self.clear()
        self.graph.set_ylabel("Rate of swelling (%/m)")
        self.graph.set_xlabel("Time (m)")

        if len(runs) == 0:
            self.canvas.draw()
            self.toolbar.update()
            return

        for run in runs:
            if not run["toshow"]:
                continue
            runname = run["runname"]
            prefix = runname + " - " if len(runs) > 1 else ""
            sensors = [sensor for _, sensor in run["sensors"].items() if sensor["toshow"]]
            for sensor in sensors:
                xs, ys = self.getDiscreteDerative(sensor["times"], sensor["pdisplacements"])
                self.graph.plot(xs, ys, label=prefix + sensor["name"])
        self.updateGraph()

    def plotAverageSwellingRate(self, runs):
        self.clear()
        self.graph.set_ylabel("Rate of swelling (%/m)")
        self.graph.set_xlabel("Time (m)")

        if len(runs) == 0:
            self.canvas.draw()
            self.toolbar.update()
            return

        runavgs = []  # [[runname, [xs], [ys]]...]
        for run in runs:
            if not run["toshow"]:
                continue
            toavgtimes = []
            toavgdisplacement = []
            sensors = [sensor for _, sensor in run["sensors"].items() if sensor["toshow"]]
            numsensors = len(sensors)
            avgxs = [sensor["times"] for sensor in sensors]
            avgys = [sensor["pdisplacements"] for sensor in sensors]
            avgxs = self.getAverages(avgxs, numsensors)
            avgys = self.getAverages(avgys, numsensors)
            xs, ys = self.getDiscreteDerative(avgxs, avgys)
            self.graph.plot(xs, ys, label=run["runname"])

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

from tkinter import *
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import numpy as np

class AnalysisGraph(Frame):
    def __init__(self, master): #master must be an AnalysisWindow
        Frame.__init__(self, master, relief=SUNKEN, borderwidth=1)
        self.master = master
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

    def plotDistances(self, runs):
        self.graph.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Displacement (%)")

        for i in range(len(runs)):
            run = runs[i]
            prefix = str(i) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
                self.graph.plot(sensor["times"], sensor["pdisplacements"], label=prefix + sensorname)
        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l, loc="upper left")
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

    def plotVoltages(self, runs):
        self.graph.clear()
        self.graph.set_xlabel("Time (m)")
        self.graph.set_ylabel("Voltage (mV)")

        for i in range(len(runs)):
            run = runs[i]
            prefix = str(i) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
                self.graph.plot(sensor["times"], sensor["voltages"], label=prefix + sensorname)
        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l, loc="upper left")
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

    def plotTotalSwells(self, runs):
        self.graph.clear()
        self.graph.set_ylabel("Total swell (%)")

        xtics = []
        totalSwells = []
        for i in range(len(runs)):
            run = runs[i]
            prefix = str(i) + " - " if len(runs) > 1 else ""
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
        self.graph.clear()
        self.graph.set_ylabel("Rate of swelling (%/m)")
        self.graph.set_xlabel("Time (m)")

        for i in range(len(runs)):
            run = runs[i]
            prefix = str(i) + " - " if len(runs) > 1 else ""
            for sensorname, sensor in run["sensors"].items():
                displacements = sensor["pdisplacements"]
                times = sensor["times"]
                rateOfChange = [(displacements[j+1] - displacements[j])/(times[j+1] - times[j]) for j in range(len(displacements) - 1)]
                self.graph.plot(sensor["times"][:-1], rateOfChange, label=prefix + sensorname)

        h, l = self.graph.get_legend_handles_labels()
        self.graph.legend(h, l)
        self.graph.autoscale(True)
        self.canvas.draw()
        self.toolbar.update()

if __name__ == '__main__':
    print("Run main.py")


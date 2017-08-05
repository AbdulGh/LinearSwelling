from tkinter import messagebox
import random
import settings
import sys
import time

try:
    import PyDAQmx
    from PyDAQmx.DAQmxFunctions import *
    from PyDAQmx.DAQmxConstants import *
except Exception as e:
    pass #handled later
        
def getFloatFromEntry(master, entry, name, mini=None, maxi=None, forceInt=False):
        s = entry.get()
        try:
            i = float(s)
            if mini is not None and i < mini:
                messagebox.showerror("Error", "Value for '" + name + "' is too small (minimum " + str(mini) + ").", parent=master)
            elif maxi is not None and i > maxi:
                messagebox.showerror("Error", "Value for '" + name + "' is too large (maximum " + str(maxi) + ").", parent=master)
            elif forceInt and not i.is_integer():
                messagebox.showerror("Error", "Value for '" + name + "' must be an integer.", parent=master)
            else:
                return i
        except ValueError:
            messagebox.showerror("Error", "Value for '" + name + "' is not numerical.", parent=master)

class DAQInput():
    def __init__(self):
        self.pydaqimported = "PyDAQmx" in sys.modules
        self.taskHandles = None
        if "PyDAQmx" in sys.modules:
            taskHandles = [TaskHandle(0) for _ in range(settings.numsensors)]
            for i in range(settings.numsensors):
                DAQmxCreateTask("",byref(taskHandles[i]))
                DAQmxCreateAIVoltageChan(taskHandles[i], settings.devicename + "/ai" + str(i+1), "", DAQmx_Val_RSE,
                                     0, settings.maxDAQoutput, DAQmx_Val_Volts, None)
                self.taskHandles = taskHandles
        #else: todo
        #    raise ImportError("Could not import PyDAQmx")

    def read(self,i):
        try:
            taskHandle = self.taskHandles[i]                    
            DAQmxStartTask(taskHandle)
            data = numpy.zeros((1,), dtype=numpy.float64)
            read = int32()
            DAQmxReadAnalogF64(taskHandle, 1, settings.maxDAQoutput, DAQmx_Val_GroupByChannel, data, 1, byref(read), None)
            DAQmxStopTask(taskHandle)
            return data[0]
        except Exception:
            return random.randint(0, 10) #todo replace this with a popup

    def close(self):
        if self.taskHandles is not None:
            for taskHandle in self.taskHandles:
                DAQmxStopTask(taskHandle)
                DAQmxClearTask(taskHandle)
            

from tkinter import *
from tkinter.ttk import *
from math import ceil, sqrt
from collections import deque
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation
from numpy import arange
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
class DAQRawOutputDialog(Toplevel):
    def __init__(self, master, daqinput):
        Toplevel.__init__(self, master)
        self.geometry("+%d+%d" % (master.winfo_rootx() + 80, master.winfo_rooty() + 80))
        self.title("Raw DAQ output")

        mainframe = Frame(self)
        mainframe.pack(padx=8, pady=8)

        #init graph
        f = plt.figure()
        #return
        f.subplots_adjust(hspace=.3)
        dimension = ceil(sqrt(settings.numsensors)) #number of plots on one side of the square grid
        self.sensoraxs = [f.add_subplot(2,2,i+1) for i in range(settings.numsensors)]
        numtodisplay = 30 #number of points on the x-axis
        initialreadings = [daqinput.read(s) for s in range(settings.numsensors)]
        self.sensorreadings = [deque([initialreadings[s] for _ in range(numtodisplay)]) for s in range(settings.numsensors)]
        xaxis = arange(numtodisplay)
        self.sensorplots = [self.sensoraxs[i].plot(xaxis, self.sensorreadings[i])[0] for i in range(settings.numsensors)]
        
        for i in range(len(self.sensoraxs)):
            ax = self.sensoraxs[i]
            ax.title.set_text("Sensor " + str(i+1))
            ax.set_xlim([0, numtodisplay])
            ax.set_ylim([0, settings.maxDAQoutput])
            ax.set_xticklabels([])

        wrapper = Frame(mainframe, relief=SUNKEN, borderwidth=1)
        canvas = FigureCanvasTkAgg(f, wrapper)
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        wrapper.pack()
        canvas.show()

        autoscaleBool = IntVar()
        def switchScaling():
            if autoscaleBool.get() == 1:
                for i in range(len(self.sensoraxs)):
                    ax = self.sensoraxs[i]
                    ax.relim()
                    ax.autoscale(enable=True, axis='y')
                    ax.autoscale_view(scaley=True, scalex=False)
                    ax.set_ylim(auto=True)
            else:
                for ax in self.sensoraxs:
                    ax.set_ylim([0, settings.maxDAQoutput])
            canvas.show()

        Checkbutton(mainframe, text="Autoscale", variable=autoscaleBool, command=switchScaling).pack(side=LEFT)
                                                                               
        def takeReading(_): #throw away frame number
            for s in range(settings.numsensors):
                queue = self.sensorreadings[s]
                queue.rotate(-1) #cycle left by one
                queue[-1] = daqinput.read(s)
                self.sensorplots[s].set_ydata(queue)

            if autoscaleBool.get() == 1:
                switchScaling()
            return self.sensorplots

        self.animation = matplotlib.animation.FuncAnimation(f, takeReading, interval=60, blit=True)
        Button(mainframe, text="Done", command=self.destroy).pack(side=RIGHT, pady=(4,0))
        self.resizable(False, False)
        
if __name__ == '__main__':
    DAQRawOutputDialog().mainloop()
    

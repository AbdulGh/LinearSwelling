from tkinter import messagebox
import random
import settings
import sys

try:
    import PyDAQmx
    from PyDAQmx.DAQmxFunctions import *
    from PyDAQmx.DAQmxConstants import *
except Exception as e:
    print("Could not import PyDAQmx. No data can be recieved from the card.") #todo make this fatal
    print("Please make sure PyDAQmx and NI-DAQ are installed.")
        
def getFloatFromEntry(master, entry, mini=None, maxi=None, forceInt=False):
        s = entry.get()
        try:
            i = float(s)
            if (mini is not None and i < mini):
                messagebox.showerror("Error", "Value for '" + entry.cname + "' is too small (minimum " + str(mini) + ")", parent=master)
            elif (maxi is not None and i > maxi):
                messagebox.showerror("Error", "Value for '" + entry.cname + "' is too large (maximum " + str(maxi) + ")", parent=master)
            elif forceInt and not i.is_integer():
                messagebox.showerror("Error", "Value for '" + entry.cname + "' must be an integer", parent=master)
            else:
                return i
        except ValueError:
            messagebox.showerror("Error", "Value for '" + entry.cname + "' is not numerical", parent=master)

class DAQInput():
    def __init__(self):
        self.pydaqimported = "PyDAQmx" in sys.modules
        self.upperLim = 10.0

        if self.pydaqimported:
            #DAQmxResetDevice("Dev1")
            taskHandles = [TaskHandle(0) for _ in range(settings.numsensors)]
            for i in range(settings.numsensors):
                DAQmxCreateTask("",byref(taskHandles[i]))
                DAQmxCreateAIVoltageChan(taskHandles[i], "Dev1/ai" + str(i+1), "", DAQmx_Val_RSE,
                                     0, self.upperLim, DAQmx_Val_Volts, None)
                self.taskHandles = taskHandles

    def read(self,i):
        if self.pydaqimported:
            taskHandle = self.taskHandles[i]                    
            DAQmxStartTask(taskHandle)
            data = numpy.zeros((1,), dtype=numpy.float64)
            read = int32()
            DAQmxReadAnalogF64(taskHandle, 1, self.upperLim, DAQmx_Val_GroupByChannel, data, 1, byref(read), None)
            DAQmxStopTask(taskHandle)
            return data[0]
        else:
            return random.randint(0,10)

if __name__ == '__main__':
    print("Run main.py")

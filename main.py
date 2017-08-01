import calibration
import analysiswindow
import measure
import tools

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *

class MainWindow(Tk): #todo fin on close
    def __init__(self):
        Tk.__init__(self)
        self.title("Swellometer")
        self.minsize(200,200)
        self.resizable(False, False)
        try:
            self.connection = tools.DAQInput()
        except ModuleNotFoundError:
            self.connection = None 
        self.initwindow()
        self.mainloop()

    def initwindow(self):
        Label(self, text="Swellometer", font="Helvetica 16").pack(pady=10)

        def calibrationOption():
            if self.connection is None:
                messagebox.showerror("Error", "Could not import PyDAQmx. No data can be recieved from the card. Make sure NI-DAQmx is installed.")
                return

            self.withdraw()
            calibrationWindow = calibration.CalibrationWindow(self, self.connection)
            self.wait_window(calibrationWindow)
            if calibrationWindow.finalParams is not None:
                experimentWindow = measure.ExperimentWindow(self, calibrationWindow.getParameters(), self.connection)
                self.wait_window(experimentWindow)
            self.deiconify()

        Button(self, text="Calibrate sensors", command=calibrationOption, width=15).pack(pady=10)

        def loadSettingsOption():
            if self.connection is None:
                messagebox.showerror("Error", "Could not import PyDAQmx. No data can be recieved from the card. Make sure NI-DAQmx is installed.", parent=self)
                return

            filename = filedialog.askopenfilename(parent=self, defaultextension=".calib", filetypes=[("Calibration File", "*.calib")])
            if filename:
                self.withdraw()

                #ExperimentWindow params are of the form [[sensornum, [x0, y0]...]...]
                #calibration files are of the form:
                #sensornum
                #x0 y0
                #...
                try:
                    with open(filename, "r") as f:
                        params = []
                        line = f.readline()
                        while line:
                            params.append(line.split(" ")[:-1]) #get rid of newline
                            line = f.readline()
                        experimentWindow = measure.ExperimentWindow(self, params, self.connection)
                except ValueError as e:
                    messagebox.showerror("Invalid file", "Could not read from this file.", parent=self)
                    self.deiconify()
                    return
                self.wait_window(experimentWindow)
                self.deiconify()

        Button(self, text="Load calibration", command=loadSettingsOption, width=15).pack(pady=10)

        def launchAnalysisWindow():
            self.withdraw()
            a = analysiswindow.AnalysisWindow()
            self.wait_window(a)
            self.deiconify()

        Button(self, text="Analyse data", command=launchAnalysisWindow, width=15).pack(pady=10)
        Button(self, text="Close", command=self.fin, width=15).pack(pady=(10, 20))

    def fin(self):
        self.connection.close()
        exit()

if __name__ == '__main__':
    MainWindow()



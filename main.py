import calibration
import settings
import measure

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *

class MainWindow(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Swellometer")
        self.minsize(200,200)
        self.resizable(False, False)
        self.initwindow()
        self.mainloop()

    def initwindow(self):
        Label(self, text="Swellometer", font="Helvetica 16").pack(pady=10)

        def calibrationOption():
            self.withdraw()
            calibrationWindow = calibration.CalibrationWindow(self)
            self.wait_window(calibrationWindow)
            if calibrationWindow.finalParams is not None:
                experimentWindow = measure.ExperimentWindow(self, calibrationWindow.getParameters()) #todo test this
                self.wait_window(experimentWindow)
            else:
                self.deiconify()

        launchCalibration = Button(self, text="Calibrate sensors", command=calibrationOption)
        launchCalibration.pack(pady=10)

        def loadSettingsOption():
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
                        sensor = int(f.readline())
                        while sensor is not None:
                            thisone = [sensor]
                            arr = f.readline().split()
                            while len(arr) == 2:
                                thisone.append([float(arr[0]), float(arr[1])])
                                arr = f.readline().split()
                            params.append(thisone)
                            if len(arr) == 1:
                                sensor = int(arr[0])
                            elif len(arr) > 2:
                                raise ValueError("Bad file")
                            else:
                                sensor = None
                        experimentWindow = measure.ExperimentWindow(self, params)
                except ValueError as e:
                    messagebox.showerror("Invalid file", "Could not read from this file.", parent=self)
                    self.deiconify()
                    return
                self.wait_window(experimentWindow)

        loadCalibration = Button(self, text="Load calibration", command=loadSettingsOption)
        loadCalibration.pack(pady=10)

        Button(self, text="Close", command=exit).pack(pady=(10, 20))

if __name__ == '__main__':
    MainWindow()



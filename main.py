import calibration
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
            calibrationWindow = calibration.CalibrationWindow(self)
            m,b = calibrationWindow.getsettings()

            calibrationWindow = calibration.CalibrationWindow(self)

        launchCalibration = Button(self, text="Calibrate sensors", command=calibrationOption)
        launchCalibration.pack(pady=10)

        def loadSettingsOption():
            f = filedialog.askopenfilename()
            m = b = None
            if f is not None:
                try:
                    m = f.readline()
                    b = f.readline()
                    m = float(m)
                    b = float(b)
                except ValueError:
                    messagebox.showerror("Invalid file", "Could not read line from this file")

            if m is not None:
                root = Tk()
                calibrationWindow = measure.ExperimentWindow(root)

        loadCalibration = Button(self, text="Load calibration", command=loadSettingsOption)
        loadCalibration.pack(pady=10)

        Button(self, text="Close", command=exit).pack(pady=10)

if __name__ == '__main__':
    MainWindow()



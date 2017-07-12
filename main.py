import calibration
import settings
import measure

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter.ttk import *

class MainWindow(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Swellometer")
        self.minsize(200,200)
        self.resizable(False, False)

        self.initwindow()

        """
        self.style = Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")"""

        self.mainloop()

    def initwindow(self):
        Label(self, text="Swellometer", font="Helvetica 16").pack(pady=10)

        def calibrationOption():
            self.withdraw()
            calibrationWindow = calibration.CalibrationWindow(self)
            self.wait_window(calibrationWindow)
            if calibrationWindow.done:
                paramList = []
                for i in range(settings.numsensors):
                    paramList.append(calibrationWindow.getSettings(i)[:2])

                experimentWindow = measure.ExperimentWindow(self, paramList)
                self.wait_window(experimentWindow)

            else:
                self.deiconify()

            #experimentWindow = measure.ExperimentWindow(self, m, b)
            #self.wait_window(experimentWindow)

        launchCalibration = Button(self, text="Calibrate sensors", command=calibrationOption)
        launchCalibration.pack(pady=10)

        def loadSettingsOption():
            f = filedialog.askopenfilename()
            if f:
                self.withdraw()
                paramList = []
                try:
                    f = open(f)
                    for i in range(settings.numsensors):
                        m = f.readline()
                        b = f.readline()
                        m = float(m)
                        b = float(b)
                        paramList.append([m,b])
                    f.close()
                except Exception as e:
                    messagebox.showerror("Invalid file", "Could not read from this file.")
                    raise e
                    self.deiconify()
                    return

                string = None
                while string is None:
                    string = simpledialog.askstring("Name", "Test name:")
                    if string is None:
                        self.deiconify()
                        return
                    elif string == "":
                        messagebox.showerror("Name", "Name cannot be empt.y")
                        string = None
                experimentWindow = measure.ExperimentWindow(self, paramList, string)
                self.wait_window(experimentWindow)

        loadCalibration = Button(self, text="Load calibration", command=loadSettingsOption)
        loadCalibration.pack(pady=10)

        Button(self, text="Close", command=exit).pack(pady=(10, 20))

if __name__ == '__main__':
    MainWindow()



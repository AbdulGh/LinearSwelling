import calibration.C
import measure

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import *

class MainWindow(Frame):
    def __init__(self):
        Frame.__init__(self)
        self.master = Tk()
        self.master.title("Swellometer")
        #self.master.resizable(False, False)

        self.initwindow()
		
		self.master.mainloop()
		
	def initwindow(self):
		Label(self.master, text="Swellometer", font="Helvetica 16").pack()

		def calibrationOption():
			root = Tk()
			calibrationWindow = calibration.CalibrationWindow(root)
			root.mainloop()

			m,b = calibrationWindow.getsettings()

			root = Tk()
			calibrationWindow = measure.ExperimentWindow(root, m, b)
			root.mainloop()
			root.grab_set()
            root.wa

		launchCalibration = Button(self.master, text="Calibrate sensors", command=calibrationOption)
		launchCalibration.pack()

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
				calibrationWindow = calibration.ExperimentWindow(root)
				root.mainloop()
				wait_window(root)


		loadCalibration = Button(self.master, text="Load calibration", command=loadSettingsOption)
		loadCalibration.pack()

		Button(self.master, text="Close", command=exit).pack()
				
			
			
	
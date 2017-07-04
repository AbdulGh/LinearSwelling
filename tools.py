from tkinter import messagebox
import random

def getFloatFromEntry(entry, mini=None, maxi=None, forceInt=False):
        s = entry.get()
        try:
            i = float(s)
            if (mini is not None and i < mini):
                messagebox.showerror("Error", "Value for '" + entry.cname + "' is too small (minimum " + str(mini) + ")")
            elif (maxi is not None and i > maxi):
                messagebox.showerror("Error", "Value for '" + entry.cname + "' is too large (maximum " + str(maxi) + ")")
            elif forceInt and not i.is_integer():
                messagebox.showerror("Error", "Value for '" + entry.cname + "' must be an integer")
            else:
                return i
        except ValueError:
            messagebox.showerror("Error", "Value for '" + entry.cname + "' is not numerical")

def getCurrentReading():
        return random.randint(0, 10)

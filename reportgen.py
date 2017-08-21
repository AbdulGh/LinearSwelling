import os
import time
from tkinter import *
from tkinter import filedialog
from tkinter import font
from tkinter import messagebox
from tkinter.ttk import *

import analysisgraph
import tools
from tools import isOne, setAll


def reportGenDialogue(runs, master):
	options = {} #runname -> False or {toShowAll, toShowAverage.. {sensorname: {sensor stuff}...]}
	for run in runs:
		name = run["runname"]
		t = Toplevel(master)
		t.title(name)
		t.resizable(False, False)
		paddingFrame = Frame(t)
		paddingFrame.pack(padx=8, pady=8)
		Label(paddingFrame, text=name).pack(side=TOP)

		runThingsFrame = Frame(paddingFrame)
		runThingsFrame.pack(side=TOP, fill=X, expand=True)

		toInclude = IntVar(value=0 if run["toshow"] else 1) #these will be swapped in the fake click that enabled/disabled everything

		def switchAll():
			setAll(paddingFrame, NORMAL if isOne(toInclude) else DISABLED)
			includeall.config(state=NORMAL)

		includeall = Checkbutton(runThingsFrame, text="Include", variable=toInclude, command=switchAll)
		includeall.invoke()
		includeall.pack(side=TOP, anchor=W)

		toShowAll = IntVar(value=1)
		Checkbutton(runThingsFrame, text="Show sensors superimposed", variable=toShowAll).pack(side=TOP, pady=(4,0), anchor=W)

		toShowAverage = IntVar(value=1)
		Checkbutton(runThingsFrame, text="Show average displacement", variable=toShowAverage).pack(side=TOP, pady=(4,0), anchor=W)

		toShowAverageRate = IntVar(value=1)
		Checkbutton(runThingsFrame, text="Show average swelling rate", variable=toShowAverageRate).pack(side=TOP, pady=(4,0), anchor=W)

		toShowTotal = IntVar(value=1)
		Checkbutton(runThingsFrame, text="Show total swells", variable=toShowTotal).pack(side=TOP, pady=(4,0), anchor=W)

		xbeginFrame = Frame(runThingsFrame)
		Label(xbeginFrame, text="x begin (m): ", width=12, anchor=W, justify=LEFT).pack(side=LEFT)
		xbeginEntry = Entry(xbeginFrame)
		xbeginEntry.insert(0, "0")
		xbeginEntry.pack(side=LEFT, pady=(0,4))

		xendFrame = Frame(runThingsFrame)
		Label(xendFrame, text="x end (m): ", width=12, anchor=W, justify=LEFT).pack(side=LEFT)
		xendEntry = Entry(xendFrame)
		xendEntry.pack(side=LEFT)		
		
		toModelAll = IntVar(value=1)
		def toggleModelAll():
			stat = NORMAL if isOne(toModelAll) else DISABLED
			xendEntry.config(state=stat)
			xbeginEntry.config(state=stat)

		mod = Checkbutton(runThingsFrame, text="Fit model", variable=toModelAll, command=toggleModelAll)
		mod.pack(side=TOP, anchor=W)
		mod.invoke()
		xbeginFrame.pack(side=TOP, anchor=W)
		xendFrame.pack(side=TOP, anchor=W)

		newFrame = True #if a new frame needs to be created next (we're placing sensors, two a row)
		currentFrame = Frame(paddingFrame)
		currentFrame.pack(side=TOP)
		sensors = {}
		for sensorname, sensor in run["sensors"].items():
			newFrame = not newFrame
			if not newFrame:
				currentFrame = Frame(paddingFrame)
				currentFrame.pack(side=TOP)

			wrapper = Frame(currentFrame, borderwidth=1, relief=RIDGE)
			wrapper.pack(side=LEFT, padx=4, pady=4)
			thisSensor = Frame(wrapper)
			thisSensor.pack(padx=4, pady=4)
			thisSensorDisable = Frame(thisSensor)
			thisDict = {"include": IntVar(value=0 if sensor["toshow"] else 1), "swelling": IntVar(value=1), "rate": IntVar(value=1)}#, "model": IntVar(value=0)}

			Label(thisSensor, text=sensorname).pack(side=TOP)

			inc = Checkbutton(thisSensor, text="Include individual", variable=thisDict["include"],
				command=lambda frame=thisSensorDisable, dic=thisDict: setAll(frame, NORMAL if isOne(dic["include"]) else DISABLED))
			inc.invoke()
			inc.pack(side=TOP)
			Checkbutton(thisSensorDisable, text="Percentage swell", variable=thisDict["swelling"]).pack(side=TOP, pady=(4,0))
			Checkbutton(thisSensorDisable, text="Swelling rates", variable=thisDict["rate"]).pack(side=TOP, pady=(4,0))
			#Checkbutton(thisSensorDisable, text="Fit model", variable=thisDict["model"]).pack(side=TOP, pady=(4,0))
			thisSensorDisable.pack(side=TOP)
			sensors[sensorname] = thisDict

		def finito():
			if toInclude.get() == 0:
				options[name] = False
			else:
				for _, sensor in sensors.items():
					for key, intvar in sensor.items():
						sensor[key] = isOne(intvar)

				findict = {"all": isOne(toShowAll), "average": isOne(toShowAverage),
							"rate": isOne(toShowAverageRate), "total": isOne(toShowTotal),
							"model": isOne(toModelAll), "sensoroptions": sensors}

				if isOne(toModelAll):
					xbegin = tools.getFloatFromEntry(master, xbeginEntry, "xbegin", mini=0)
					xend = tools.getFloatFromEntry(master, xendEntry, "xend", mini=0)

					if xbegin is None or xend is None:
						return

					findict["xbegin"] = xbegin
					findict["xend"] = xend

				options[name] = findict
			t.destroy()

		Button(paddingFrame, text="Confirm", command=finito).pack(side=TOP, anchor=E)

		master.wait_window(t)
	return options

def genReport(runs, options, foldername, agraph):
	os.makedirs(foldername)
	os.makedirs(foldername + "/images")

	olddir = os.getcwd()
	os.chdir(foldername)

	with open("report.html", "w") as f:
		imgdir = tools.uniqueName("images")
		os.makedirs(imgdir)
		if len(runs) > 1:
			f.write("<h1>Run comparison</h1>")
			f.write("<h3>Swelling</h3>")
			agraph.plotAverageDistance(runs)
			name = tools.uniqueName(imgdir + "/all.png")
			agraph.fig.savefig(name)
			f.write("<img src='" + name + "' alt='All'>")

			f.write("<h3>Rates</h3>")
			agraph.plotAverageSwellingRate(runs)
			name = tools.uniqueName(imgdir + "/rates.png")
			agraph.fig.savefig(name)
			f.write("<img src='" + name + "' alt='Rates'>")

			f.write("<h1>Individual runs</h1>")
		for run in runs:
			runname = run["runname"]
			thisrunoptions = options[runname]

			if not run["toshow"]:
				continue
			alone = [run]
			prefix = tools.uniqueName(imgdir + "/" + runname)
			os.makedirs(prefix)
			f.write("<h2>" + runname + "</h2>")
			f.write("<p>Time: " + time.strftime("%a, %d %b %Y %H:%M:%S", run["timeofrun"]) + "</p>")

			sensors = [sensor for sensor in run["sensors"].values()]
			for sensor in sensors:
				sensor["toshow"] = True

			if thisrunoptions["all"]:
				f.write("<h3>All sensors</h3>")
				agraph.plotDistances(alone)
				name = tools.uniqueName(prefix + "/all.png")
				agraph.fig.savefig(name)
				f.write("<img src='" + name + "' alt='All'>")

			if thisrunoptions["average"]:
				f.write("<h3>Average swelling</h3>")
				agraph.plotAverageDistance(alone)
				name = tools.uniqueName(prefix + "/average.png")
				agraph.fig.savefig(name)
				f.write("<img src='" + name + "' alt='Average'>")

			if thisrunoptions["rate"]:
				f.write("<h3>Average swelling rate</h3>")
				agraph.plotAverageSwellingRate(alone)
				name = tools.uniqueName(prefix + "/averagerate.png")
				agraph.fig.savefig(name)
				f.write("<img src='" + name + "' alt='Average Rate'>")

			if thisrunoptions["total"]:
				f.write("<h3>Total swells</h3>")
				agraph.plotTotalSwells(alone)
				name = tools.uniqueName(prefix + "/total.png")
				agraph.fig.savefig(name)
				f.write("<img src='" + name + "' alt='Total'>")

			if thisrunoptions["model"]:
				f.write("<h3>Fit attempt</h3>")
				f.write("<p>See 'Analytical solution for clay plug swelling experiments'</p>")
				a,b = agraph.fitModel(alone, thisrunoptions["xbegin"], thisrunoptions["xend"])[runname]
				name = tools.uniqueName(prefix + "/model.png")
				agraph.fig.savefig(name)
				f.write("<img src='" + name + "' alt='Model'>")
				f.write("<p>(Alpha: " + str(a) + " - Beta: " + str(b) + ")</p>")

			for sensor in sensors:
				sensor["toshow"] = False
				os.makedirs(prefix + "/" + sensor["name"])
			for sensor in sensors:
				thissensoroptions = thisrunoptions["sensoroptions"][sensor["name"]]

				if not thissensoroptions["include"]:
					continue

				sensor["toshow"] = True
				f.write("<h3>" + sensor["name"] + "</h3>")
				f.write("<p>Final swell: " + str(sensor["pdisplacements"][-1]) + "%</p>")

				if thissensoroptions["swelling"]:
					f.write("<h4>Swelling</h4>")
					agraph.plotDistances(alone)
					name = tools.uniqueName(prefix + "/" + sensor["name"] + "/displacement.png")
					agraph.fig.savefig(name)
					f.write("<img src='" + name + "' alt='Displacement'>")

				if thissensoroptions["rate"]:
					f.write("<h4>Swelling rate</h4>")
					agraph.plotRatePercentageSwell(alone)
					name = tools.uniqueName(prefix + "/" + sensor["name"] + "/rate.png")
					agraph.fig.savefig(name)
					f.write("<img src='" + name + "' alt='Rate'>")

				sensor["toshow"] = False
		
		f.close()
	agraph.graph.clear()
	os.chdir(olddir)
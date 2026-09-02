import customtkinter as ctk
from utils import general
import sys, json

jobFile = general.pathInfo("jsonAuth")+"jobs.json"
deviceFile = general.pathInfo("jsonAuth")+"devices.json"

class Overlay(ctk.CTk):
    def __init__(self, deviceName, deviceIP, jobID):
        super().__init__()

        self.jobID = jobID
        self.deviceName = deviceName
        self.ip = deviceIP

        self.infoFont = ctk.CTkFont(family="consolas", size=15, weight="bold")
        self.dataFont = ctk.CTkFont(family="consolas", size=15, weight="normal")

        self.geometry("400x200")
        self.configure(fg_color="black")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.createLabels()
        self.createButtons()

    def createLabels(self):
        self.infoContainer = ctk.CTkFrame(self, fg_color="black")
        self.infoContainer.grid(row=0, column=0, sticky="nsew", padx=(10, 10))
        color = "black"

        self.infoContainer.grid_rowconfigure((0, 1), weight=1)
        self.infoContainer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self.infoContainer, text="Device Name: ", font=self.infoFont, fg_color=color).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(self.infoContainer, text="IP Address: ", font=self.infoFont, fg_color=color).grid(row=2, column=0, sticky="w")

        ctk.CTkLabel(self.infoContainer, text=self.deviceName, font=self.dataFont, fg_color=color).grid(row=0, column=1, sticky="e")
        ctk.CTkLabel(self.infoContainer, text=self.ip, font=self.dataFont, fg_color=color).grid(row=2, column=1, sticky="e")

    def createButtons(self):
        self.buttonContainer = ctk.CTkFrame(self)
        self.buttonContainer.grid(row=1, column=0)
        self.grid_columnconfigure((0, 1), weight=1)

        rejectButton = ctk.CTkButton(self.buttonContainer, text="Reject", fg_color="red", command=self.rejectJob)
        rejectButton.grid(row=0, column=0)

        acceptButton = ctk.CTkButton(self.buttonContainer, text="Accept", fg_color="green", command=self.admitJob)
        acceptButton.grid(row=0, column=1)

    def admitJob(self):
        jobs = general.readJSON(jobFile)
        jobs[self.jobID]["Status"] = "Accepted"
        general.writeJSON(jobFile, jobs)
        self.destroy()

    def rejectJob(self):
        try:
            jobs = general.readJSON(jobFile)
            jobs[self.jobID]["Status"] = "Rejected"
            general.writeJSON(jobFile, jobs)
            self.destroy()
        except Exception as e:
            print(self.jobID, self.deviceName, self.ip)
            raise e

def submitRequest(job):
    name, ip, jobID = job["Device Name"], job["IP Address"], job["Job ID"]
    overlay = Overlay(name, ip, jobID)

    overlay.mainloop()

if __name__ == "__main__":
    job = json.loads(sys.argv[1])
    submitRequest(job)
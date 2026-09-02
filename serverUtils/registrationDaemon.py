from utils import general
import threading, time, subprocess, json

jobFile = general.pathInfo("jsonAuth")+"jobs.json"
deviceFile = general.pathInfo("jsonAuth")+"devices.json"

class Daemon:
    def run(self):
        while True:
            jobs = general.readJSON(jobFile)

            for jobID in jobs:
                if jobs[jobID]["Status"] != "Pending":
                    continue
                launchGUI(jobs[jobID])
                jobs[jobID]["Status"] = "Request Sent"
                break

            general.writeJSON(jobFile, jobs)
            time.sleep(5)

def launchGUI(job):
    subprocess.Popen([
        r"C:\Server\.venv\Scripts\python.exe",
        r"C:\Server\registrationUI.py",
        json.dumps(job)
    ])

if __name__ == "__main__":
    daemon = Daemon()
    daemon.run()
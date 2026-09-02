from utils.imports import *
import utils.general as general

router = APIRouter()
jobFile = general.pathInfo("jsonAuth")+"jobs.json"
deviceFile = general.pathInfo("jsonAuth")+"devices.json"

class content(BaseModel):
    name: str
    ip: str

def registerDevice(deviceName):
    deviceID = str(uuid.uuid4())
    deviceKey = str(uuid.uuid4())

    devices = general.readJSON(deviceFile)
    devices[deviceID] = {
        "deviceName": deviceName,
        "deviceKey": deviceKey
    }

    general.writeJSON(deviceFile, devices)

    return deviceID, deviceKey

def addJob(jobID, deviceName, ip):
    jobs = general.readJSON(jobFile)
    jobs[jobID] = {
        "Status": "Pending",
        "Device Name": deviceName, 
        "IP Address": ip,
        "Job ID": jobID
        }
    general.writeJSON(jobFile, jobs)

@router.post("/register/new")
def registerNew(content: content):
    jobID = str(uuid.uuid4())

    addJob(jobID, content.name, content.ip)

    return {"Status": "Job Pending", "JobID": jobID}

@router.get("/register/check")
def registerCheck(jobID: str = Header()):
    jobs = general.readJSON(jobFile)

    if jobID not in jobs:
        return {
            "status code": 404,
            "status": "Job not found"
        }

    if jobs[jobID]["Status"] == "Rejected":
        return {
            "status code": 401,
            "status": "Access Denied"
        }
    elif jobs[jobID]["Status"] == "Pending" or jobs[jobID]["Status"] == "Request Sent":
        return {
            "status code": 202,
            "status": "Pending action"
            }

    deviceID, deviceKey = registerDevice(jobs[jobID]["Device Name"])

    jobs.pop(jobID)
    general.writeJSON(jobFile, jobs)

    return {
        "status code": 200,
        "status": "Succesfully Registered",
        "deviceKey": deviceKey,
        "deviceID": deviceID
        }
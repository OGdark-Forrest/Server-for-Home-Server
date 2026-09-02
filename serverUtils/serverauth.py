from fastapi import HTTPException
import utils.general as general

def getKey(deviceID):
    devices = general.readJSON(general.pathInfo("jsonAuth")+"devices.json")
    if deviceID not in devices:
        return None
    return devices[deviceID]["deviceKey"]

def verifyKey(deviceID, userKey):
    key = getKey(deviceID)

    if not key:
        raise HTTPException(404, detail="Invalid Key/DeviceID")

    if userKey != key:
        raise HTTPException(400, detail="Invalid Key/DeviceID")
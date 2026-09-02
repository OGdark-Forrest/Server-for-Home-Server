from utils.imports import *

class copyFile:
    def __init__(self, router, dbHandler):
        self.router = router
        self.dbHandler = dbHandler
        self.schema = """
        File Start:
        {
        "params": {
            "fileID": str,
            "fileName": str,
            "directory": str
            "numberOfChunks": int
        }
    }
        Chunk:
        {
        "params": {
            "chunkNumber": int,
            "fileID": str    
        },
        "data": {
            "chunkData": bytes|str
        }
    }"""
        self.files = {}

    def call(self, job):
        self.job = job
        self.router.updateStatus("files/copysingle", "BUSY")
        try:
            output = self.checkAppendFileDictionary()
            if self.checkEnd():
                completeFile = self.reconstructFile()
                output = self.createFile(completeFile)
                del self.files[self.job["params"]["fileID"]]
            resultStatus = "SUCCESS"
        except Exception as e:
            output = str(e)
            resultStatus = "ERROR"

        finally:
            self.job["result"] = output
            self.job["resultStatus"] = resultStatus
            self.dbHandler.addRecord(self.job)
            self.router.updateStatus("files/copysingle", "AVAILABLE")

    def checkAppendFileDictionary(self):
        params = self.job["params"]
        if "fileName" in params:
            self.files[params["fileID"]] = {
                "fileName": params["fileName"],
                "numberOfChunks": params["numberOfChunks"],
                "directory": params["directory"],
                "chunks": [None]*params["numberOfChunks"]
            }
            return "File Entry Created"

        data = self.job["data"]
        self.files[params["fileID"]]["chunks"][params["chunkNumber"]-1] = base64.b64decode(data["chunkData"])
        return "Chunk Added Successfully"

    def checkEnd(self):
        currFileIDInfo = self.files[self.job["params"]["fileID"]]
        if None in currFileIDInfo["chunks"]:
            return False
        return True

    def reconstructFile(self):
        currFileIDInfo = self.files[self.job["params"]["fileID"]]
        complete = b"".join(currFileIDInfo["chunks"])
        return complete

    def createFile(self, completeFile):
        currFileIDInfo = self.files[self.job["params"]["fileID"]]
        os.makedirs(currFileIDInfo["directory"], exist_ok=True)

        with open(currFileIDInfo["directory"]+currFileIDInfo["fileName"], "wb") as wfile:
            wfile.write(completeFile)

        return f'File {currFileIDInfo["fileName"]} saved under directory {currFileIDInfo["directory"]}'

    def getStatus(self):
        return "AVAILABLE"
class Replace:
    def __init__(self, router, resultManager):
        self.router = router
        self.resultManager = resultManager
        self.schema = """{
        "params": {
            "string": str,
            "toReplace": str,
            "substitute": str
        }
        }"""

    def setJob(self, job):
        self.job = job

    def call(self):
        self.router.updateStatus("txtproc/replace", "BUSY")
        try:
            params = self.job["params"]
            string = params["string"]
            toReplace = params["toReplace"]
            substitute = params["substitute"]

            output = string.replace(toReplace, substitute)
            resultStatus = "SUCCESS"
        except Exception as e:
            output = str(e)
            resultStatus = "ERROR"

        finally:
            self.job["result"] = output
            self.job["resultStatus"] = resultStatus
            self.resultManager.addResult(self.job)
            self.router.updateStatus("txtproc/replace", "AVAILABLE")

    def getStatus(self):
        return "AVAILABLE"
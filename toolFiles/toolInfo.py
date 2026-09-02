class GetTools:
    def __init__(self, router, resultManager):
        self.router = router
        self.resultManager = resultManager
        self.schema = "params: {'type': BUSY|AVAILABLE|DOWN|ALL}"

    def setJob(self, job):
        self.job = job

    def call(self):
        self.router.updateStatus("toolinfo/getall", "BUSY")
        try:
            targetStatus = self.job["params"]["type"]
            if targetStatus.upper() not in ["BUSY", "AVAILABLE", "DOWN", "ALL"]:
                output = "Invalid Type selected"
                resultStatus = "ERROR"
            else:
                output = {}
                for endpoint in self.router.routingTable:
                    info = self.router.routingTable[endpoint]
                    if targetStatus.upper() != "ALL":
                        if info["status"] != targetStatus:
                            continue
                    output[endpoint] = {"toolInfo": info["toolInfo"], "status": info["status"]}
                resultStatus = "SUCCESS"
        except Exception as e:
            output = str(e)
            resultStatus = "ERROR"

        finally:
            self.job["result"] = output
            self.job["resultStatus"] = resultStatus
            self.resultManager.addResult(self.job)
            self.router.updateStatus("toolinfo/getall", "AVAILABLE")

    def getStatus(self):
        return "AVAILABLE"

class getToolSchema:
    def __init__(self, router, resultManager):
        self.router = router
        self.resultManager = resultManager
        self.schema = """{
        "params": {
            "endpoint": str
        }
        }"""

    def setJob(self, job):
        self.job = job

    def call(self):
        self.router.updateStatus("toolinfo/getSchema", "BUSY")
        try:
            targetEndpoint = self.job["params"]["endpoint"]
            if targetEndpoint not in self.router.routingTable:
                output = f"Target endpoint {targetEndpoint} not found"
                resultStatus = "SUCCESS"
            else:
                output = self.router.routingTable[targetEndpoint]["toolObj"].schema
                resultStatus = "SUCCESS"
        except Exception as e:
            output = str(e)
            resultStatus = "ERROR"

        finally:
            self.job["result"] = output
            self.job["resultStatus"] = resultStatus
            self.resultManager.addResult(self.job)
            self.router.updateStatus("toolinfo/getSchema", "AVAILABLE")

    def getStatus(self):
        return "AVAILABLE"
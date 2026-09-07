class Test:
    def __init__(self, router, resultManager):
        self.router = router
        self.resultManager = resultManager
        self.schema = """
            Anything
        """

    def setJob(self, job):
        self.job = job

    def call(self):
        self.router.updateStatus("test", "BUSY")
        try:
            output = self.job
            resultStatus = "SUCCESS"
        except Exception as e:
            output = str(e)
            resultStatus = "ERROR"

        finally:
            self.job["result"] = output
            self.job["resultStatus"] = resultStatus
            self.resultManager.addResult(self.job)
            self.router.updateStatus("test", "AVAILABLE")

    def getStatus(self):
        return "AVAILABLE"
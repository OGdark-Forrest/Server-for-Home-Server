from utils import general
from utils.imports import *

from toolFiles.textProcessing import Replace
from toolFiles.toolInfo import getToolSchema, GetTools
from toolFiles.fileTransfer import copyFile
from toolFiles.test import Test

class WebSocketConnection:
    def __init__(self):
        self.isConnected = None
        self.logger = general.setLogger("HomeServerArch.py: WebSocketConnection")

    async def startConnection(self, websocket:WebSocket):
        try:
            await websocket.accept()
            self.isConnected = True
            self.websocket = websocket
            self.logger.info("Connected to Client")
            self.setComponents()
            self.logger.info("Set listener components")
        except Exception as e:
            self.logger.exception(str(e))

    def setComponents(self):
        self.jobHandler = general.tableHandler(general.pathInfo("db")+"server.db", "jobs")
        self.jobSelector = Selector(self.jobHandler)

        self.resultHandler = general.tableHandler(general.pathInfo("db")+"server.db", "results")
        self.router = Router(self.resultHandler)
        self.resultSelector = Selector(self.resultHandler)

        self.webSocketListener = Listener(self.websocket, self)
        self.webSocketSender = Sender(self.websocket, self)

    async def startLoop(self):
        await asyncio.gather(
            self.startListen(),
            self.processJobs(),
            self.sendResults()
        )

    async def startListen(self):
        self.logger.info("Started listener")
        while True:
            message = await self.webSocketListener.listen()
            if message == "DOWN":
                await asyncio.sleep(2)
                self.logger.critical("Reattempting sender connection")
            elif message == "NONE":
                await asyncio.sleep(1)
            else:
                self.logger.info("Received job")
                self.jobHandler.addRecord(message)

    async def processJobs(self):
        self.logger.info("Started job process")
        while True:
            job = self.jobSelector.get()

            if job is None:
                await asyncio.sleep(1)
                continue

            self.logger.info("Selected job being sent to router")

            while True:
                status = self.router.route(job)

                if status == "JOB ROUTED":
                    self.logger.info(job)
                    self.jobHandler.deleteRecord(job["requestID"])
                    self.logger.info("JOB ROUTED AND DELETED FROM QUEUE")
                    break
                elif status == "DOWN":
                    self.jobHandler.deleteRecord(job["id"])
                    self.jobHandler.addRecord(job)
                    self.logger.warning(f"Endpoint {job["requestID"]} is DOWN")
                    break
                else:
                    await asyncio.sleep(1)

    async def sendResults(self):
        self.logger.info("Started sender")
        while self.isConnected:
            result = self.resultSelector.get()

            if result is None:
                await asyncio.sleep(0.1)
                continue

            self.logger.info("Received result to send")
            status = await self.webSocketSender.send(result)
            if status == "DOWN":
                await asyncio.sleep(2)
                self.logger.critical("Reattempting sender connection")
            elif status == "NONE":
                await asyncio.sleep(1)
            else:
                self.resultHandler.deleteRecord(result["requestID"])

class Selector:
    """
    In charge of getting job
    """
    def __init__(self, tableHandler: general.tableHandler):
        self.tableHandler = tableHandler

    def get(self):
        for i in range(1, 5):
            job = self.tableHandler.getRecordByVal(["priority"], [i])
            if job is not None:
                break
        return job

class Router:
    """
    In charge of routing the jobs to the respective tools and calling Selector.

    Routing Table Schema:
    {
        "endpoint": {
            "status": AVAILABLE|BUSY|DOWN,
            "toolObj": <object>,
            "toolInfo": str
        }
        .
        .
        .
    }
    """
    def __init__(self, tableHandler:general.tableHandler):
        self.tableHandler = tableHandler
        self.routingTable = {
            "txtproc/replace": {
                "status": "NONE",
                "toolObj": Replace(self, self.tableHandler),
                "toolInfo": "Replaces characters in a string"
            },
            "toolinfo/getall": {
                "status": "NONE",
                "toolObj": GetTools(self, self.tableHandler),
                "toolInfo": "Gets endpoints in routing table according to status type"
            },
            "toolinfo/getSchema": {
                "status": "NONE",
                "toolObj": getToolSchema(self, self.tableHandler),
                "toolInfo": "Gets the schema of a specified endpoint"
            },
            "files/copysingle": {
                "status": "NONE",
                "toolObj": copyFile(self, self.tableHandler),
                "toolInfo": "Copies a file into home server"
            },
            "test": {
                "status": "NONE",
                "toolObj": Test(self, self.tableHandler),
                "toolInfo": "Miscellaneous"
            }
        }
        self.logger = general.setLogger("HomeServerArch.py: Router")
        self.initStatus()

    def isReady(self, job):
        return self.routingTable[job["endpoint"]]["status"]

    def initStatus(self):
        for endpoint in self.routingTable:
            try:
                toolObj = self.routingTable[endpoint]["toolObj"]
                self.routingTable[endpoint]["status"] = toolObj.getStatus()
            except Exception as e:
                self.logger.exception(str(e))
                self.routingTable[endpoint]["status"] = "DOWN"
        self.logger.info("Done Initializing")

    def updateStatus(self, endpoint, status):
        self.routingTable[endpoint]["status"] = status

    def route(self, job):
        if self.isReady(job) == "AVAILABLE":
            toolInfo = self.routingTable[job["endpoint"]]
            self.callTool(toolInfo["toolObj"], job)
            return "JOB ROUTED"

        return self.isReady(job)

    def callTool(self, toolObj, job):
        self.updateStatus(job["endpoint"], "BUSY")
        toolObj.setJob(job)
        threading.Thread(
            target=toolObj.call,
            daemon=True
        ).start()
        self.logger.debug("Started thread")

class Listener:
    """
    Responsible for receiving data over a websocket connection.
    """
    def __init__(self, websocket: WebSocket, webSocketConnection: WebSocketConnection):
        self.logger = general.setLogger("HomeServerArch.py: Listener")
        self.webSocketConnection = webSocketConnection
        self.websocket = websocket
        self.isListening = None

    async def listen(self):
        try:
            self.isListening = True
            while True:
                job = await self.websocket.receive_text()
                return json.loads(job)
        except:
            if self.webSocketConnection.isConnected is True:
                self.logger.critical("LISTENER IS DOWN")
                self.webSocketConnection.isConnected = False
                return "DOWN"
            self.isListening = False
            self.webSocketConnection.isConnected = False
            return "NONE"

class Sender:
    """
    Responsible for sending data over a websocket connection.
    """
    def __init__(self, websocket: WebSocket, webSocketConnection: WebSocketConnection):
        self.webSocketConnection = webSocketConnection
        self.websocket = websocket
        self.isSending = None
        self.logger = general.setLogger("HomeServerArch.py: Sender")

    async def send(self, data: dict):
        try:
            await self.websocket.send_json(data)
            self.isSending = True
            return "SUCCESSFUL"
        except:
            returnStatus = None
            if self.webSocketConnection.isConnected is True:
                self.logger.critical("SENDER IS DOWN")
                returnStatus = "DOWN"
            self.isSending = False
            self.webSocketConnection.isConnected = False
            returnStatus = "NONE"
            return returnStatus
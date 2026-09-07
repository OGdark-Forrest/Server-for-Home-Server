from utils import general
from utils.imports import *

from toolFiles.textProcessing import Replace
from toolFiles.toolInfo import getToolSchema, GetTools
from toolFiles.fileTransfer import copyFile
from toolFiles.test import Test

class WebSocketConnection:
    def __init__(self):
        self.isConnected = None

    async def startConnection(self, websocket:WebSocket):
        try:
            await websocket.accept()
            self.isConnected = True
            self.websocket = websocket
            self.setComponents()
        except Exception as e:
            raise e

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
        while True:
            message = await self.webSocketListener.listen()
            self.jobHandler.addRecord(message)

    async def processJobs(self):
        while True:
            job = self.jobSelector.get()

            if job is None:
                await asyncio.sleep(1)
                continue

            while True:
                if self.router.isReady(job) == "AVAILABLE":
                    self.router.route(job)
                    self.jobHandler.deleteRecord(job["id"])
                    break
                elif self.router.isReady(job) == "DOWN":
                    self.jobHandler.addRecord(job)
                    break
                else:
                    await asyncio.sleep(1)

    async def sendResults(self):
        while self.isConnected:
            result = self.resultSelector.get()

            if result is None:
                await asyncio.sleep(0.1)
                continue

            await self.webSocketSender.send(result)
            self.resultHandler.deleteRecord(result["id"])

class Selector:
    """
    In charge of getting job
    """
    def __init__(self, tableHandler: general.tableHandler):
        self.tableHandler = tableHandler

    def get(self):
        return self.tableHandler.getAnyRecord()

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
        self.initStatus()

    def isReady(self, job):
        return self.routingTable[job["endpoint"]]["status"]

    def initStatus(self):
        for endpoint in self.routingTable:
            try:
                toolObj = self.routingTable[endpoint]["toolObj"]
                self.routingTable[endpoint]["status"] = toolObj.getStatus()
            except:
                self.routingTable[endpoint]["status"] = "DOWN"

    def updateStatus(self, endpoint, status):
        self.routingTable[endpoint]["status"] = status

    def route(self, job):
        toolInfo = self.routingTable[job["endpoint"]]

        return self.callTool(toolInfo["toolObj"], job)

    def callTool(self, toolObj, job):
        self.updateStatus(job["endpoint"], "BUSY")

        threading.Thread(
            target=toolObj.call,
            args=(job, ),
            daemon=True
        ).start()

class Listener:
    """
    Responsible for receiving data over a websocket connection.
    """
    def __init__(self, websocket: WebSocket, webSocketConnection):
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
            print("Websocket Disconnected")
            self.isListening = False
            self.webSocketConnection.isConnected = False

class Sender:
    """
    Responsible for sending data over a websocket connection.
    """
    def __init__(self, websocket: WebSocket, webSocketConnection):
        self.webSocketConnection = webSocketConnection
        self.websocket = websocket
        self.isSending = None

    async def send(self, data: dict):
        try:
            await self.websocket.send_json(data)
            self.isSending = True
        except:
            self.isSending = False
            self.webSocketConnection.isConnected = False
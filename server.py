from utils.imports import *
from utils import general

import serverUtils.register as register
from serverUtils.serverauth import verifyKey
from HomeServerArch import WebSocketConnection

general.configureLogger("serverLog.log", "INFO")

server = FastAPI()
server.include_router(register.router)

@server.get("/")
def initiateConnection():
    return {"status": "Connection successful"}
@server.websocket("/initWSS")
async def initHandshake(websocket: WebSocket, deviceKey: str = Header(), deviceID: str = Header()):
    verifyKey(deviceID, deviceKey)
    webSocketConnection = WebSocketConnection()
    await webSocketConnection.startConnection(websocket=websocket)
    await webSocketConnection.startLoop()

if __name__ == "__main__":
    uvicorn.run(server, port=8005, host="0.0.0.0")
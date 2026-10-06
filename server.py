from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI()

clients = []

bus_position = {
    "bus_id": "BUS-001",
    "latitude": None,
    "longitude": None
}

@app.get("/gps")
async def gps_page():
    return FileResponse("gps.html")



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    clients.append(websocket)

    print("Client connecté")

    try:

        while True:

            position = await websocket.receive_json()

            bus_position["latitude"] = position["latitude"]
            bus_position["longitude"] = position["longitude"]

            print(
                "📍 Position du bus :",
                bus_position["latitude"],
                bus_position["longitude"]
            )

            # Envoyer la position à tous les clients
            for client in clients:

                await client.send_json(
                    bus_position
                )

    except WebSocketDisconnect:

        if websocket in clients:
            clients.remove(websocket)

        print("Client déconnecté")
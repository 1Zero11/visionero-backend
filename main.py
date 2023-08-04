import os
import jsons
import signal
import subprocess
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
import glob
from fastapi.responses import HTMLResponse
import psutil
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
import ntpath
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from executable import Executable
from launch import Launch
import threading
from fastapi_utils.tasks import repeat_every

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# anki = Launch(path="D:\\Programs\\Anki\\anki.exe", launch_time=datetime.now(), type=True)

engine = create_engine("postgresql://run:password@localhost:5432/run", echo=True)

apps = []

SQLModel.metadata.create_all(engine)

def select_launches():
    with Session(engine) as session:
        statement = select(Launch)
        results = session.exec(statement)
        return results.all()
            


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message, websocket: WebSocket):
        text = jsons.dumps(message)
        await websocket.send_text(text)

    async def broadcast(self, message):
        for connection in self.active_connections:
            text = jsons.dumps(message)
            await connection.send_text(text)
            
manager = ConnectionManager()

@app.get("/")
async def get():
    return {"message": "Hey!"}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    await manager.send_personal_message(apps, websocket)
    try:
        while True:
            data = await websocket.receive_json()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.on_event("startup")
@app.get("/path")
async def get_items():
    global apps
    
    if(apps == []):
        desktop_folder = "C:/Users/79910/Desktop"
        shortcut_files = glob.glob(desktop_folder + "/*.lnk")
        app_paths = [subprocess.check_output(['powershell', '-command', '(New-Object -COM WScript.Shell).CreateShortcut("{}").TargetPath'.format(shortcut)]).decode().strip() for shortcut in shortcut_files]
        apps = [Executable(path=path, id=idx) for idx, path in enumerate(app_paths)]
        print(jsons.dump(apps))
    
    return apps

@app.get("/history")
async def get_history():
    launches = select_launches()
    return launches
    

@app.get("/startApp")
async def launch_app(id: int = 0):
    global engine
    
    path = apps[id].path
    exe_name, tail = ntpath.split(path)
    
    if not (tail in (p.name() for p in psutil.process_iter())):
        process = subprocess.Popen(path)
        
        launch_data = Launch(path=tail, launch_time=datetime.now(), type=True)
        with Session(engine) as session:
            session.add(launch_data)
            session.commit()
        
        return {"message": "Application launched successfully."}
    else:
        return {"message": "Process is already running."}
    
@app.get("/stopApp")
async def close_app(id: int = 0):
    
    path = apps[id].path
    if path != "":
        exe_name, tail = ntpath.split(path)
        for p in psutil.process_iter():
            if p.name() == tail:
                p.kill()
                launch_data = Launch(path=p.name(), launch_time=datetime.now(), type=False)
                with Session(engine) as session:
                    session.add(launch_data)
                    session.commit()
                return {"mesage": "stopped"}
    return {"mesage": "not found"}
                    
def refresh_running():
    for app in apps:
        _, tail = ntpath.split(app.path)
        app.is_running = check_running_by_name(tail)

def check_running_by_name(name: str):
    return name in (p.name() for p in psutil.process_iter())
    

@app.on_event("startup")
@repeat_every(seconds=5)
async def refresh_task():
    global manager
    refresh_running()
    #print("Hey")
    await manager.broadcast(apps)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
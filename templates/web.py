#!/usr/bin/env python3
import os
import subprocess
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pyantic import Basemodel

app = FastAPI(title="P9 Control Panel")
templates = Jinja2Templates(directory="templates")

TARGET_MAC="BA:0F:2B:68:94:F7"
FIFO_PATH="tmp/p9_notifications"

class notificacion(BaseModel):
    mensaje: str

@app.get("/", response_class="HTMLResponse")
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html",{"reqyest":request})
@app.get("/api/status")
async def get_status():
    estado = {"conectado":false,
              "bateria":"N/A"
            }
try:
    resultado = subprocess.run(

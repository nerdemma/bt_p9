#!/usr/bin/env python3

import asyncio
import os
import re
import subprocess
import sys
from gtts import gTTS

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
TARGET_MAC = "BA:0F:2B:68:94:F7"
FIFO_PATH = "/tmp/p9_notifications"

CMD_PAUSE = ["playerctl", "pause"]
CMD_PLAY = ["playerctl", "play"]

CONNECTED_REGEX = re.compile(rf"Device {TARGET_MAC} Connected: yes", re.IGNORECASE) 
DISCONECTED_REGEX = re.compile(rf"Device {TARGET_MAC} Connected: no", re.IGNORECASE)

# Estado global en memoria
is_p9_connected = False
cola_notificaciones = []

def verificar_conexion_inicial() -> bool:
    
    try:
        result = subprocess.run(
            ["bluetoothctl", "info", TARGET_MAC],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        if re.search(r"Connected:\s+yes", result.stdout, re.IGNORECASE):
            print(f"[INIT] Estado inicial detectado: Los P9 YA están conectados.")
            return True
        else:
            print(f"[INIT] Estado inicial detectado: Los P9 están desconectados.")
            return False
    except Exception as e:
        print(f"[WARN] No se pudo verificar el estado inicial: {e}")
        return False


def control_media(action: str):

    cmd = CMD_PLAY if action == "play" else CMD_PAUSE
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[MEDIA] Accion ejecutada con exito {action.upper()}")
    except FileNotFoundError:
        print("[ERROR] 'playerctl' no esta instalado o no se encuentra en el PATH")


def hablar(texto: str):

    archivo_mp3 = "/tmp/p9_tts_temp.mp3"
    try:
        print(f"[TTS] Generando audio para: '{texto}'")
        tts = gTTS(text=texto, lang='es', slow=False)
        tts.save(archivo_mp3)
        
        subprocess.run(["mpv", "--no-video", archivo_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(archivo_mp3):
            os.remove(archivo_mp3)
    except Exception as e:
        print(f"[ERROR TTS] No se pudo procesar la notificación: {e}")


def procesar_cola_pendientes():
    global cola_notificaciones
    if not cola_notificaciones:
        return
    print("[BUFFER] Procesando {len(cola_notificaciones)} notificaciones acumuladas")

    cuerpo_mensaje = "Tenias las siguientes notificaciones pendientes:"
    cuerpo_mensaje+=". ".join(cola_notificaciones) + "."
    cola_notificaciones.clear()
    hablar(cuerpo_mensaje)


async def escuchar_notificaciones():

    global is_p9_connected, cola_notificaciones

    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)
        os.chmod(FIFO_PATH, 0o666)

    print(f"[INIT] Escuchando notificaciones en pipe: {FIFO_PATH}")

    fd = os.open(FIFO_PATH, os.O_RDONLY | os.O_NONBLOCK)
    pipe_reader = open(fd, 'r', encoding='utf-8')

    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    def al_recibir_datos():

        while True:
            line = pipe_reader.readline()
            if not line:
                break
            texto = line.strip()
            if texto:
                loop.call_soon_threadsafe(queue.put_nowait, texto)


    loop.add_reader(fd, al_recibir_datos)

    try:

        while True:
            texto = await queue.get()
            print(f"[PIPE] Recibido: '{texto}'")
            if is_p9_connected:
                hablar(texto)
            else:
                print(f"[PIPE] P9 desconectados. Almacenado en cola buffer: '{texto}'")
                cola_notificaciones.append(texto)
    finally:
        loop.remove_reader(fd)
        pipe_reader.close()
        

async def monitor_bluetooth():

    global is_p9_connected
    
    print(f"[INIT] iniciando monitoreo para el dispositivo P9 [{TARGET_MAC}]...")
    process = await asyncio.create_subprocess_exec(
        "bluetoothctl", "monitor",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    try:
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            line = line_bytes.decode('utf-8', errors='ignore').strip()

            if CONNECTED_REGEX.search(line):
                print(f"[EVENT] Audiculares P9 conectados.")
                is_p9_connected = True
                control_media("play")
                await asyncio.sleep(1.5)
                procesar_cola_pendientes()


            elif DISCONECTED_REGEX.search(line):
                print(f"[EVENT] Audiculares P9 desconectados")
                is_p9_connected = False
                control_media("pause")
                
    except asyncio.CancelledError:
        print("\n[SHUTDOWN] Cancelando la tarea del monitoreo...")
    finally:
        if process.returncode is None:
            try:
                process.terminate()
                await process.wait()
            except ProcessLookupError:
                pass
        print("[SHUTDOWN] Monitor detenido limpiamente")


async def main_async():

    await asyncio.gather(
        monitor_bluetooth(),
        escuchar_notificaciones()
    )


def main():
    global is_p9_connected

    if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", TARGET_MAC):
        print(f"[CRITICAL] La direccion MAC '{TARGET_MAC}' no es valida. Edita el script", file=sys.stderr)
        sys.exit(1)
        
    is_p9_connected = verificar_conexion_inicial()

    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n [EXIT] Script interrumpido por el usuario. ")


if __name__ == "__main__":
    main()
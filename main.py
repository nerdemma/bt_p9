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

# Estado global en memoria para validar si los auriculares están listos para hablar
is_p9_connected = False


def verificar_conexion_inicial()->bool:
    try:
        result = subprocess.run(
            ["bluetoothctl","info",TARGET_MAC],
            stdout = subprocess.PIPE,
            stderr = subprocess.DEVNULL,
            text=


        )








def control_media(action: str):
    """Controla la reproducción de música mediante playerctl."""
    cmd = CMD_PLAY if action == "play" else CMD_PAUSE
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[MEDIA] Accion ejecutada con exito {action.upper()}")
    except FileNotFoundError:
        print("[ERROR] 'playerctl' no esta instalado o no se encuentra en el PATH")


def hablar(texto: str):
    """Genera el audio a partir de texto y lo reproduce."""
    archivo_mp3 = "/tmp/p9_tts_temp.mp3"
    try:
        print(f"[TTS] Generando audio para: '{texto}'")
        tts = gTTS(text=texto, lang='es', slow=False)
        tts.save(archivo_mp3)
        
        # mpv enviará el audio al dispositivo por defecto actual (tus P9 si están conectados)
        subprocess.run(["mpv", "--no-video", archivo_mp3], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(archivo_mp3):
            os.remove(archivo_mp3)
    except Exception as e:
        print(f"[ERROR TTS] No se pudo procesar la notificación: {e}")


async def escuchar_notificaciones():
    """Escucha de manera persistente el Named Pipe (FIFO) sin consumir CPU."""
    global is_p9_connected

    # Creamos el Pipe con los permisos adecuados si no existe
    if not os.path.exists(FIFO_PATH):
        os.mkfifo(FIFO_PATH)
        os.chmod(FIFO_PATH, 0o666)

    print(f"[INIT] Escuchando notificaciones en pipe: {FIFO_PATH}")

    while True:
        try:
            # Abrimos el canal de lectura de forma asíncrona
            reader, _ = await asyncio.open_fifo_read_pipe(FIFO_PATH)
            
            while True:
                line = await reader.readline()
                if not line:
                    # Fin de archivo (EOF). Volvemos al bucle externo para esperar un nuevo escritor.
                    break
                
                texto = line.decode('utf-8').strip()
                if texto:
                    print(f"[PIPE] Recibido: '{texto}'")
                    # CONDICIÓN DE SEGURIDAD: Solo habla si los auriculares están realmente conectados
                    if is_p9_connected:
                        hablar(texto)
                    else:
                        print(f"[PIPE] P9 desconectados. Notificación ignorada: '{texto}'")
                        
        except Exception as e:
            print(f"[ERROR PIPE] {e}")
            
        # Espera estratégica para evitar bucles infinitos agresivos en caso de fallos del sistema de archivos
        await asyncio.sleep(0.5)


async def monitor_bluetooth():
    """Monitorea el flujo de eventos de bluetoothctl de forma reactiva."""
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
    """Lanza ambas subtareas en el mismo loop de eventos asíncronos."""
    await asyncio.gather(
        monitor_bluetooth(),
        escuchar_notificaciones()
    )


def main():
    if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", TARGET_MAC):
        print(f"[CRITICAL] La direccion MAC '{TARGET_MAC}' no es valida. Edita el script", file=sys.stderr)
        sys.exit(1)
    try:
        # Ejecutamos el punto de entrada asíncrono unificado
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n [EXIT] Script interrumpido por el usuario. ")


if __name__ == "__main__":
    main()
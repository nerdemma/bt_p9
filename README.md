# P9 Bluetooth Media Monitor & TTS Agent 🎧🚀

Un demonio asíncrono y liviano escrito en Python para **Debian** diseñado para automatizar el control multimedia y proporcionar un sistema de notificaciones por voz (*Text-to-Speech*) interactuando de forma reactiva con el subsistema de Bluetooth (`BlueZ`) y controladores MPRIS.

## ✨ Características principales

- **Monitoreo Reactivo (Event-Driven):** Escucha eventos del kernel a través de `bluetoothctl monitor` usando `asyncio`. No realiza *polling* continuo, logrando un consumo de **0% CPU** en reposo.
- **Sincronización Cold Start:** Verifica el estado real de conexión de los auriculares P9 inmediatamente al arrancar el servicio.
- **Control Inteligente Multimedia:** Pausa la música automáticamente si los auriculares se desconectan (vía `playerctl`) y reanuda la reproducción al reconectarse.
- **Servidor de Notificaciones Privadas (IPC):** Expone un *Named Pipe* (`FIFO`) en Unix. Cualquier script del sistema puede enviarle texto en tiempo real para que el demonio lo convierta a voz (`gTTS`) y lo reproduzca exclusivamente en los auriculares de forma aislada.

## 📋 Tabla de contenidos

- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Despliegue como Servicio Systemd](#despliegue-como-servicio-systemd)
- [Integración y Notificaciones](#integración-y-notificaciones)
- [Licencia](#licencia)

## 🛠️ Requisitos del Sistema

El script utiliza herramientas nativas del ecosistema de Linux:

```bash
sudo apt update
sudo apt install bluez playerctl mpv python3 python3-venv -y
```

| Componente | Propósito |
|-----------|----------|
| **bluez** | Gestión de Bluetooth de Linux |
| **playerctl** | Control universal de reproductores de música en Linux (Spotify, VLC, navegadores, etc.) |
| **mpv** | Reproductor multimedia minimalista para la salida de audio TTS |
| **python3** | Intérprete de Python 3.8+ |
| **python3-venv** | Herramienta para crear entornos virtuales aislados |

## 🚀 Instalación

### 1. Clonar el repositorio y configurar el directorio

```bash
mkdir -p ~/projects/bt_p9
cd ~/projects/bt_p9
# Clona el repositorio o descarga el archivo main.py en esta ruta
git clone <tu-repo-url> .
```

### 2. Configurar el Entorno Virtual (Aislado de Debian)

Para evitar conflictos con el gestor de paquetes de Debian (`externally-managed-environment`), encapsulamos las dependencias:

```bash
python3 -m venv ~/.p9_env
~/.p9_env/bin/pip install -U pip
~/.p9_env/bin/pip install gTTS
```

## ⚙️ Configuración

### Obtener la dirección MAC de tus auriculares P9

1. Enciende tus auriculares P9
2. Ejecuta el siguiente comando para listar todos los dispositivos Bluetooth:

```bash
bluetoothctl devices
```

Deberías ver una salida similar a:
```
Device 00:00:00:00:00:00 P9 Headphones
```

3. Edita el archivo `main.py` y actualiza la constante global con tu MAC:

```python
TARGET_MAC = "00:00:00:00:00:00"  # Reemplaza con tu MAC real
```

## 🔧 Despliegue como Servicio Systemd

Para mantener el script corriendo de manera persistente en segundo plano bajo tu sesión de usuario:

### 1. Crear el archivo de configuración del servicio

```bash
mkdir -p ~/.config/systemd/user/
nano ~/.config/systemd/user/p9-monitor.service
```

### 2. Pegar la siguiente estructura

Reemplaza `emmanuel` por tu usuario real:

```ini
[Unit]
Description=Monitor de Conexión de Auriculares P9 con TTS
After=bluetooth.target

[Service]
ExecStart=/home/emmanuel/.p9_env/bin/python3 /home/emmanuel/projects/bt_p9/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

### 3. Recargar y activar el servicio

```bash
systemctl --user daemon-reload
systemctl --user enable --now p9-monitor.service
```

### 4. Verificar logs y telemetría en tiempo real

```bash
# Ver estado actual del servicio
systemctl --user status p9-monitor.service

# Ver logs en tiempo real
journalctl --user -u p9-monitor.service -f
```

## 🔔 Integración: Enviar Notificaciones de Voz

La arquitectura utiliza un canal de comunicación entre procesos (IPC Named Pipe) en `/tmp/p9_notifications`. El servicio procesará cualquier entrada de texto únicamente si llevas puestos los auriculares.

### Desde la Terminal (CLI)

```bash
echo "Hola Emmanuel, el sistema de notificaciones está operativo." > /tmp/p9_notifications
```

### Desde otro Script de Python

Puedes integrar alertas a tus proyectos de desarrollo (ej. monitor de servidores, batería baja, webhooks):

```python
import os

def enviar_alerta_p9(mensaje):
    """Envía una notificación de voz al demonio P9."""
    pipe_path = "/tmp/p9_notifications"
    if os.path.exists(pipe_path):
        with open(pipe_path, "w") as pipe:
            pipe.write(f"{mensaje}\n")
    else:
        print(f"Advertencia: El pipe {pipe_path} no existe. ¿Está corriendo el servicio?")

# Ejemplo de uso
enviar_alerta_p9("Alerta del sistema: La base de datos local ha sido respaldada.")
```

## 📊 Casos de Uso

Algunos ejemplos prácticos de integración:

- **Alertas de Sistema:** Notificaciones de batería baja, actualizaciones disponibles, etc.
- **Webhooks:** Integración con servicios en línea para alertas push
- **Monitor de Servidores:** Notificaciones de eventos críticos en tus servidores
- **Automatizaciones:** Control automático de reproducción de audio basado en eventos

## 🐛 Troubleshooting

| Problema | Solución |
|----------|----------|
| El servicio no inicia | Verifica los logs con `journalctl --user -u p9-monitor.service -f` |
| No se reconocen los auriculares | Asegúrate de que la MAC es correcta en `main.py` |
| No hay sonido en las notificaciones | Verifica que `mpv` esté instalado y que los auriculares estén conectados |
| Errores de permisos | Comprueba que el venv tiene permisos correctos (`chmod +x ~/.p9_env/bin/python3`) |

## 📝 Licencia

Desarrollado bajo licencia **MIT**. Libre para uso, modificación y distribución personal.

---

**¿Necesitas ayuda?** Abre un [issue](../../issues) en el repositorio.

**¿Tienes mejoras?** Las pull requests son bienvenidas 🎉

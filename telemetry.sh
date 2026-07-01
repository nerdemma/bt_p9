#!/usr/bin/bash
FIFO_PATH="/tmp/p9_notifications"

enviar_alerta()
{
if [ -p "$FIFO_PATH" ]; then
	echo "$1" > "$FIFO_PATH"
fi
}

case "$1" in
	hora)
		HORA=$(date+"%H y %M minutos")
		enviar_alerta "Emmanuel, la hora actual es: $HORA"
		;;
	status)
	       	CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
		RAM=$(free -m | awk '/Mem/ {print int ($3/$2 * 100)')
		enviar_alerta "Estado del sistema: Uso de CPU al $CPU por ciento, y memoria RAM al $RAM por ciento"
	bateria)
	BAT=$(bluetoothctl info BA:0F:2B:68:94:F7 | grep "Battery Percentage" | awk -F '[()]' '{print $2}')
	
	if[-z "$BAT" ]; then
	enviar_alerta "No se pudo obtener el porcentaje de bateria de los audiculares."
	else
	enviar_alerta "La carga de tus audiculares P9 es del $BAT porciento."
	fi
	;;
	*)
	echo "Uso: $0 {hora|status|bateria}"
	;;
esac



#!/bin/bash

set -e

if [ ! -f .env ]; then
    echo ".env no encontrado"
    exit 1
fi

set -a
source .env
set +a

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo "No se encontró el venv en '$PROJECT_ROOT/venv'. Creálo con: python3 -m venv venv"
    exit 1
fi

# ---------------------------------------------------------
# 1. Verificar si Redis ya está escuchando en REDIS_PORT
# ---------------------------------------------------------
redis_esta_corriendo() {
    # Usamos /dev/tcp, una feature nativa de bash, en vez de nc,
    # para no depender de que netcat esté instalado.
    (exec 3<>"/dev/tcp/${REDIS_HOST:-127.0.0.1}/${REDIS_PORT}") 2>/dev/null
    local resultado=$?
    exec 3>&- 2>/dev/null
    return $resultado
}

if redis_esta_corriendo; then
    echo "Redis ya está corriendo en el puerto ${REDIS_PORT}."
else
    echo "Redis no está corriendo. Levantando docker-compose..."

    if ! docker info >/dev/null 2>&1; then
        echo "No se puede acceder al daemon de Docker (¿problema de permisos en /var/run/docker.sock?)."
        echo "Probá: sudo usermod -aG docker \$USER   (y reiniciar sesión), o corré este script con sudo."
        exit 1
    fi

    docker compose up -d

    # Esperar a que el puerto realmente responda antes de seguir
    echo "Esperando a que Redis esté listo..."
    for i in $(seq 1 15); do
        if redis_esta_corriendo; then
            echo "Redis inicializado correctamente."
            break
        fi
        sleep 1
        if [ "$i" -eq 15 ]; then
            echo "Redis no respondió a tiempo en el puerto ${REDIS_PORT}."
            exit 1
        fi
    done
fi

# ---------------------------------------------------------
# 2. Comandos a correr, cada uno en su propia terminal
# ---------------------------------------------------------
CMD_CONN_MANAGER="cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && python3 -m server.connection.conn_manager"
CMD_WORKER="cd '$PROJECT_ROOT' && source '$PROJECT_ROOT/venv/bin/activate' && celery -A server.celery.celery_app worker -Q enriquecimiento,persistencia,estadistica --loglevel=info"

abrir_terminal() {
    local titulo="$1"
    local comando="$2"

    # Escribimos el comando a un script temporal en vez de pasarlo inline.
    # Esto evita romper el escaping cuando hyprctl/kitty re-parsean el string
    # (comillas anidadas dentro de comillas anidadas se rompen fácil).
    local script_tmp
    script_tmp="$(mktemp /tmp/peer-guard-XXXXXX.sh)"
    {
        echo "#!/bin/bash"
        echo "$comando"
        echo "exec bash"
    } > "$script_tmp"
    chmod +x "$script_tmp"

    if command -v tmux >/dev/null 2>&1; then
        # Sesión tmux con dos ventanas, una por proceso. Conectate con: tmux attach -t peer-guard
        if tmux has-session -t peer-guard 2>/dev/null; then
            tmux new-window -t peer-guard -n "$titulo" "$script_tmp"
        else
            tmux new-session -d -s peer-guard -n "$titulo" "$script_tmp"
        fi
    elif command -v hyprctl >/dev/null 2>&1 && [ -n "$XDG_CURRENT_DESKTOP" ] && command -v kitty >/dev/null 2>&1; then
        # Hyprland: lanzamos kitty (o $TERMINAL si está seteado) vía hyprctl
        # para que respete tus window rules en vez de un fork suelto.
        local term_bin="${TERMINAL:-kitty}"
        hyprctl dispatch exec -- "$term_bin" --title "$titulo" "$script_tmp"
    elif [ -n "$TERMINAL" ] && command -v "$TERMINAL" >/dev/null 2>&1; then
        "$TERMINAL" --title "$titulo" "$script_tmp" &
    elif command -v kitty >/dev/null 2>&1; then
        kitty --title "$titulo" "$script_tmp" &
    elif command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal --title="$titulo" -- "$script_tmp"
    elif command -v konsole >/dev/null 2>&1; then
        konsole --new-tab -p tabtitle="$titulo" -e "$script_tmp" &
    elif command -v xterm >/dev/null 2>&1; then
        xterm -T "$titulo" -e "$script_tmp" &
    else
        echo "No se encontró tmux, hyprctl+kitty, \$TERMINAL, ni una terminal gráfica soportada."
        echo "Corré esto manualmente en una terminal nueva:"
        echo "  $comando"
        return 1
    fi
}

abrir_terminal "conn_manager" "$CMD_CONN_MANAGER"
abrir_terminal "celery_worker" "$CMD_WORKER"

if command -v tmux >/dev/null 2>&1; then
    echo "Procesos levantados en sesión tmux 'peer-guard'."
    echo "Para verlos: tmux attach -t peer-guard"
else
    echo "Procesos levantados en terminales separadas."
fi

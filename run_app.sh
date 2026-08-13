#!/bin/bash
export DATABASE_URL="postgresql://rentas_user:rentas_password@localhost:5432/rentas_db"
export SECRET_KEY="mi_super_secreto_local"
export PORT=5000
cd /mnt/ssd/Documents/Administracion_Rentas
./venv/bin/gunicorn app:app --bind 0.0.0.0:$PORT --workers 3 > app.log 2>&1 &
echo $! > app.pid
echo "Application started on port $PORT with PID $!"

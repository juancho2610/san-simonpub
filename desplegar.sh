#!/usr/bin/env bash
# Actualiza el servidor: trae el código, instala, migra y reinicia.
set -euo pipefail
cd /srv/san_simon_pub
git pull --ff-only
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy || true
sudo systemctl restart san-simon-pub
sleep 4
curl -s -o /dev/null -w "Portada: %{http_code}\n" -H "Host: sansimonpub.com" -H "X-Forwarded-Proto: https" http://127.0.0.1:8000/

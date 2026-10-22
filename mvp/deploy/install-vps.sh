#!/usr/bin/env bash
set -euo pipefail

APP=/opt/esparragos
DOMAIN=esparragos.comextech.es
if [[ -e "$APP/app.py" || -e "/etc/nginx/sites-enabled/$DOMAIN" ]]; then
  echo "Ya existe un despliegue de esparragos; no se sobrescribe automáticamente." >&2
  exit 1
fi

mkdir -p "$APP/data"
tar -xzf /tmp/esparragos-mvp-produccion.tar.gz -C "$APP" --no-same-owner
python3 -m venv --system-site-packages "$APP/.venv"
"$APP/.venv/bin/python" -m pip install --no-cache-dir --no-deps 'ultralytics==8.4.66' 'ultralytics-thop' 'selenium>=4.20,<5' 'pdfplumber>=0.11,<1' >/tmp/esparragos-pip.log 2>&1 || {
  tail -n 40 /tmp/esparragos-pip.log >&2
  exit 1
}
"$APP/.venv/bin/python" -m pip install --no-cache-dir --no-deps --index-url https://download.pytorch.org/whl/cpu 'torchvision==0.26.0+cpu' >>/tmp/esparragos-pip.log 2>&1
"$APP/.venv/bin/python" -m pip install --no-cache-dir polars psutil trio trio-websocket pdfminer.six pypdfium2 >>/tmp/esparragos-pip.log 2>&1
"$APP/.venv/bin/python" -m pip install --no-cache-dir --ignore-installed --no-deps 'pypdf==6.20.0' >>/tmp/esparragos-pip.log 2>&1

chown -R root:root "$APP"
chown www-data:www-data "$APP/data"
chmod 750 "$APP/data"
install -m 644 /tmp/esparragos.service /etc/systemd/system/esparragos.service
install -m 644 /tmp/esparragos.nginx.conf "/etc/nginx/sites-available/$DOMAIN"

ln -s "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
nginx -t
systemctl daemon-reload
systemctl enable --now esparragos.service
systemctl reload nginx
echo "Instalación terminada. Configura HTTPS con Certbot para el dominio."

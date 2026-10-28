#!/usr/bin/env bash
set -euo pipefail
curl -sS --resolve esparragos.comextech.es:443:127.0.0.1 \
  -o /tmp/esparragos-home.html \
  -w 'public_https=%{http_code}\n' \
  https://esparragos.comextech.es/
grep -q 'Vigía Espárrago' /tmp/esparragos-home.html
curl -sS --resolve esparragos.comextech.es:443:127.0.0.1 \
  -o /tmp/esparragos-comparison.json \
  -w 'comparison_https=%{http_code}\n' \
  https://esparragos.comextech.es/api/model-comparison
python3 - <<'PY'
import json
report = json.load(open('/tmp/esparragos-comparison.json'))
print('external_hits', report['baseline']['hit_count'], report['candidate']['hit_count'])
PY

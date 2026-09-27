#!/usr/bin/env bash
# Backend (/health) va saytni tekshiradi: har bir qism uchun bitta qator
# chiqaradi, birortasi ishlamasa exit 1. Workflow ham, lokal ham ishlatadi:
#   bash .github/scripts/monitor.sh
set -uo pipefail

BACKEND_HEALTH_URL="${BACKEND_HEALTH_URL:-https://futbol-xabar-backend.onrender.com/health}"
SITE_URL="${SITE_URL:-https://futbolxabar.uz/}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# "/" emas, /health: "/" baza yiqilganda ham 200 qaytaradi, /health esa bazaga
# ulanib ko'radi va "database":"ok" deydi.
#
# Render Free uxlab qolgan bo'lsa uyg'onishi ~1 daqiqa, shuning uchun bir necha
# urinish. Eng yomon holat 3×60 + 2×10 = 200 s — workflow timeout'idan qisqa
# bo'lishi shart: aks holda GitHub job'ni "cancelled" qiladi va sabab logga
# chiqmay qoladi (sentabrdagi uzilish ikki hafta shunday sezilmay turgan).
check_backend() {
  local attempt code reason
  for attempt in 1 2 3; do
    rm -f "$tmp/health.json"
    code="$(curl -sS --max-time 60 -o "$tmp/health.json" -w '%{http_code}' \
      "$BACKEND_HEALTH_URL" 2>"$tmp/curl.err")"
    if [[ "$code" == "200" ]] && grep -q '"database":"ok"' "$tmp/health.json" 2>/dev/null; then
      echo "✅ Backend: ishlayapti"
      return 0
    fi
    if [[ "$attempt" -lt 3 ]]; then sleep 10; fi
  done

  # 503 bo'lsa /health sababni o'zi aytadi (database_error — JSON'dagi oxirgi
  # kalit); javob umuman kelmasa, curl xatosi.
  reason="$(sed -n '/"database_error":"/{s/.*"database_error":"//;s/"}$//;s/[\]"/"/g;p}' "$tmp/health.json" 2>/dev/null)"
  if [[ -z "$reason" ]]; then
    reason="$(tail -n 1 "$tmp/curl.err" | tr -d '\r')"
  fi
  echo "❌ Backend: HTTP $code${reason:+ — $reason}"
  return 1
}

# Sayt (Vercel): kutilgani 200. Vercel o'zi to'xtatgan bo'lsa (402 va h.k.)
# x-vercel-error sarlavhasi sababini aytadi, masalan DEPLOYMENT_DISABLED.
check_site() {
  local attempt code reason
  for attempt in 1 2; do
    rm -f "$tmp/site.headers"
    code="$(curl -sS -L --max-time 30 -o /dev/null -D "$tmp/site.headers" \
      -w '%{http_code}' "$SITE_URL" 2>"$tmp/curl.err")"
    if [[ "$code" == "200" ]]; then
      echo "✅ Sayt: ishlayapti"
      return 0
    fi
    if [[ "$attempt" -lt 2 ]]; then sleep 5; fi
  done

  reason="$(grep -i '^x-vercel-error:' "$tmp/site.headers" 2>/dev/null | tail -n 1 | cut -d: -f2- | tr -d ' \r')"
  if [[ -z "$reason" ]]; then
    reason="$(tail -n 1 "$tmp/curl.err" | tr -d '\r')"
  fi
  echo "❌ Sayt: HTTP $code${reason:+ — $reason}"
  return 1
}

status=0
check_backend || status=1
check_site || status=1
exit "$status"

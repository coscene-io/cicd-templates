#!/usr/bin/env bash

set -Eeuo pipefail

readonly MAX_PAYLOAD_BYTES=20000

error() {
  printf '::error::%s\n' "$*" >&2
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    error "Required command is unavailable: ${command_name}"
    exit 1
  fi
}

if [[ -z "${FEISHU_WEBHOOK_URL:-}" ]]; then
  error 'Missing required input: webhook-url'
  exit 1
fi

if [[ "$FEISHU_WEBHOOK_URL" != https://* ]]; then
  error 'Feishu webhook URL must use HTTPS'
  exit 1
fi

if [[ -z "${FEISHU_TEXT:-}" ]]; then
  error 'Missing required input: text'
  exit 1
fi

require_command curl
require_command jq

payload="$(jq -cn --arg text "$FEISHU_TEXT" \
  '{msg_type: "text", content: {text: $text}}')"
payload_bytes="$(printf '%s' "$payload" | wc -c | tr -d '[:space:]')"

if ((payload_bytes > MAX_PAYLOAD_BYTES)); then
  error "Feishu payload exceeds ${MAX_PAYLOAD_BYTES} bytes: ${payload_bytes}"
  exit 1
fi

payload_file="$(mktemp)"
response_file="$(mktemp)"
trap 'rm -f -- "$payload_file" "$response_file"' EXIT

printf '%s' "$payload" >"$payload_file"

if ! http_code="$(
  curl \
    --silent \
    --show-error \
    --proto '=https' \
    --connect-timeout 5 \
    --max-time 20 \
    --header 'Content-Type: application/json; charset=utf-8' \
    --data-binary "@${payload_file}" \
    --output "$response_file" \
    --write-out '%{http_code}' \
    "$FEISHU_WEBHOOK_URL"
)"; then
  error 'Feishu webhook transport failure'
  exit 1
fi

if [[ ! "$http_code" =~ ^2[0-9]{2}$ ]]; then
  error "Feishu webhook HTTP failure: ${http_code}"
  exit 1
fi

if ! jq -e 'type == "object"' "$response_file" >/dev/null 2>&1; then
  error 'Feishu webhook returned an invalid JSON response'
  exit 1
fi

if ! jq -e '
  def is_zero: . == 0 or . == "0";
  if has("code") then
    .code | is_zero
  elif has("StatusCode") then
    .StatusCode | is_zero
  else
    false
  end
' "$response_file" >/dev/null; then
  error_details="$(
    jq -r '
      "Feishu rejected request: code=\(.code // .StatusCode // "missing") " +
      "message=\((.msg // .StatusMessage // "missing") | tostring | gsub("[\r\n]"; " "))"
    ' "$response_file"
  )"
  error "$error_details"
  exit 1
fi

printf 'Feishu notification sent successfully.\n'

export const DEBUG_LOG_LIMIT = 150;
export const DEBUG_DEPTH_LIMIT = 5;
export const SECRET_SCAN_LIMIT = 20;
export const DEBUG_ARRAY_LIMIT = 20;
export const DEBUG_STRING_LIMIT = 2000;

function shouldRedactKey(key) {
  if (!key) {
    return false;
  }
  const normalized = String(key).toLowerCase();
  if (normalized === "authorization" || normalized === "proxy-authorization") {
    return true;
  }
  if (normalized === "api_key" || normalized === "apikey" || normalized === "x-api-key") {
    return true;
  }
  if (normalized.endsWith("_key") || normalized.endsWith("apikey")) {
    return true;
  }
  return (
    normalized.includes("token") ||
    normalized.includes("secret") ||
    normalized.includes("password") ||
    normalized.includes("bearer")
  );
}

export function redactStringSecrets(value) {
  if (value === null || value === undefined) {
    return value;
  }
  let out = String(value);
  out = out.replace(
    /([?&](?:key|api_key|apikey|token|access_token|authorization)=)[^&#\s]+/gi,
    "$1REDACTED"
  );
  out = out.replace(/\b(Bearer)\s+[A-Za-z0-9\-._~+/]+=*/gi, "$1 REDACTED");
  out = out.replace(
    /\b(api_key|apikey|access_token|token|authorization|auth)\b\s*[:=]\s*[^\s,;]+/gi,
    "$1=[REDACTED]"
  );
  return out;
}

const SECRET_PATTERNS = [
  /([?&](?:key|api_key|apikey|token|access_token|authorization)=)(?!REDACTED)[^&#\s]+/i,
  /\b(Bearer)\s+(?!REDACTED)[A-Za-z0-9\-._~+/]+=*/i,
  /\b(api_key|apikey|access_token|token|authorization|auth)\b\s*[:=]\s*(?!\[REDACTED\]|REDACTED)[^\s,;]+/i,
];

function containsSecretString(value) {
  if (value === null || value === undefined) {
    return false;
  }
  return SECRET_PATTERNS.some((pattern) => pattern.test(String(value)));
}

function scanSecrets(value, path, findings, depth = 0) {
  if (findings.length >= SECRET_SCAN_LIMIT || value === null || value === undefined) {
    return;
  }
  if (depth > DEBUG_DEPTH_LIMIT) {
    return;
  }
  if (typeof value === "string") {
    if (containsSecretString(value)) {
      findings.push(path || "root");
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((entry, index) => {
      if (findings.length < SECRET_SCAN_LIMIT) {
        scanSecrets(entry, `${path}[${index}]`, findings, depth + 1);
      }
    });
    return;
  }
  if (typeof value === "object") {
    Object.entries(value).forEach(([key, entry]) => {
      if (findings.length < SECRET_SCAN_LIMIT) {
        scanSecrets(entry, path ? `${path}.${key}` : key, findings, depth + 1);
      }
    });
  }
}

export function scrubSecretsValue(value, depth = 0) {
  if (depth > DEBUG_DEPTH_LIMIT) {
    return "[Truncated]";
  }
  if (value === null || value === undefined) {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((entry) => scrubSecretsValue(entry, depth + 1));
  }
  if (typeof value === "object") {
    const output = {};
    Object.entries(value).forEach(([key, entry]) => {
      output[key] = shouldRedactKey(key)
        ? "[REDACTED]"
        : scrubSecretsValue(entry, depth + 1);
    });
    return output;
  }
  if (typeof value === "string") {
    return redactStringSecrets(value);
  }
  return value;
}

export function redactValue(value, depth = 0) {
  if (depth > DEBUG_DEPTH_LIMIT) {
    return "[Truncated]";
  }
  if (value === null || value === undefined) {
    return value;
  }
  if (Array.isArray(value)) {
    const slice = value.slice(0, DEBUG_ARRAY_LIMIT).map((entry) => redactValue(entry, depth + 1));
    if (value.length > DEBUG_ARRAY_LIMIT) {
      slice.push(`[${value.length - DEBUG_ARRAY_LIMIT} more items]`);
    }
    return slice;
  }
  if (typeof value === "object") {
    const output = {};
    Object.entries(value).forEach(([key, entry]) => {
      output[key] = shouldRedactKey(key) ? "[REDACTED]" : redactValue(entry, depth + 1);
    });
    return output;
  }
  if (typeof value === "string") {
    const scrubbed = redactStringSecrets(value);
    if (scrubbed.length > DEBUG_STRING_LIMIT) {
      return `${scrubbed.slice(0, DEBUG_STRING_LIMIT)}...`;
    }
    return scrubbed;
  }
  return value;
}

export function redactErrorMessage(message) {
  return redactStringSecrets(message || "");
}

export function formatTracePayload(payload, traceRedact) {
  const safePayload = traceRedact ? redactValue(payload) : payload;
  if (safePayload === undefined) {
    return "undefined";
  }
  return JSON.stringify(safePayload, null, 2);
}

export function buildSecretAudit({
  debugEntries = [],
  history = [],
  lastErrorMessage = "",
  lastErrorDetail = null,
  error = "",
  uiResourceError = "",
  auditRestLog = [],
  rejectedBridgeEvents = [],
}) {
  const findings = [];
  scanSecrets(debugEntries, "debugEntries", findings);
  scanSecrets(history, "history", findings);
  scanSecrets(lastErrorMessage, "lastErrorMessage", findings);
  scanSecrets(lastErrorDetail, "lastErrorDetail", findings);
  scanSecrets(error, "error", findings);
  scanSecrets(uiResourceError, "uiResourceError", findings);
  scanSecrets(auditRestLog, "auditRestLog", findings);
  scanSecrets(rejectedBridgeEvents, "rejectedBridgeEvents", findings);
  return {
    count: findings.length,
    paths: findings.slice(0, 6),
    truncated: findings.length >= SECRET_SCAN_LIMIT,
  };
}

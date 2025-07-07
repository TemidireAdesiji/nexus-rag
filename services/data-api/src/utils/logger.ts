type LogLevel = "debug" | "info" | "warn" | "error";

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
};

let currentLevel: LogLevel = "info";

function setLevel(level: LogLevel): void {
  currentLevel = level;
}

function shouldLog(level: LogLevel): boolean {
  return LOG_LEVELS[level] >= LOG_LEVELS[currentLevel];
}

function formatMessage(
  level: LogLevel,
  message: string,
  meta?: Record<string, unknown>
): string {
  const entry = {
    timestamp: new Date().toISOString(),
    level: level.toUpperCase(),
    message,
    ...meta,
  };
  return JSON.stringify(entry);
}

function debug(message: string, meta?: Record<string, unknown>): void {
  if (shouldLog("debug")) {
    process.stdout.write(formatMessage("debug", message, meta) + "\n");
  }
}

function info(message: string, meta?: Record<string, unknown>): void {
  if (shouldLog("info")) {
    process.stdout.write(formatMessage("info", message, meta) + "\n");
  }
}

function warn(message: string, meta?: Record<string, unknown>): void {
  if (shouldLog("warn")) {
    process.stderr.write(formatMessage("warn", message, meta) + "\n");
  }
}

function error(message: string, meta?: Record<string, unknown>): void {
  if (shouldLog("error")) {
    process.stderr.write(formatMessage("error", message, meta) + "\n");
  }
}

export const logger = {
  debug,
  info,
  warn,
  error,
  setLevel,
};

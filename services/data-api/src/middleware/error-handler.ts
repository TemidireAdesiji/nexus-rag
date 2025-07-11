import { Request, Response, NextFunction } from "express";
import { logger } from "../utils/logger.js";
import type { RequestWithId } from "../types/index.js";

export function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction): void {
  const requestId = (req as RequestWithId).requestId || "unknown";
  const statusCode = "statusCode" in err ? (err as Error & { statusCode: number }).statusCode : 500;

  logger.error("Unhandled error", {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    requestId,
  });

  res.status(statusCode).json({
    error: statusCode === 500 ? "Internal server error" : err.message,
    statusCode,
    requestId,
  });
}

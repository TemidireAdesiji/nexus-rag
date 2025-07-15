import { Response, NextFunction } from "express";
import { env } from "../config.js";
import type { RequestWithId } from "../types/index.js";

const UNPROTECTED_PREFIXES = ["/auth/", "/ping", "/docs", "/swagger"];

export function authMiddleware(req: RequestWithId, res: Response, next: NextFunction): void {
  const isUnprotected = UNPROTECTED_PREFIXES.some((prefix) => req.path.startsWith(prefix));

  if (isUnprotected) {
    next();
    return;
  }

  const authHeader = req.headers.authorization;

  if (!authHeader) {
    res.status(401).json({
      error: "Authorization header is required",
      statusCode: 401,
      requestId: req.requestId || "unknown",
    });
    return;
  }

  const parts = authHeader.split(" ");
  if (parts.length !== 2 || parts[0] !== "Bearer") {
    res.status(401).json({
      error: "Authorization header must use Bearer scheme",
      statusCode: 401,
      requestId: req.requestId || "unknown",
    });
    return;
  }

  const token = parts[1];
  if (token !== env.API_BEARER_TOKEN) {
    res.status(403).json({
      error: "Invalid bearer token",
      statusCode: 403,
      requestId: req.requestId || "unknown",
    });
    return;
  }

  next();
}

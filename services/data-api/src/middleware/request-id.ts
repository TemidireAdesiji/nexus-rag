import { Response, NextFunction } from "express";
import { v4 as uuidv4 } from "uuid";
import type { RequestWithId } from "../types/index.js";

export function requestIdMiddleware(req: RequestWithId, res: Response, next: NextFunction): void {
  const requestId = (req.headers["x-request-id"] as string | undefined) || uuidv4();
  req.requestId = requestId;
  res.setHeader("X-Request-ID", requestId);
  next();
}

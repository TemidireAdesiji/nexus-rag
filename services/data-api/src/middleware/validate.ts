import { Request, Response, NextFunction } from "express";
import { ZodSchema, ZodError } from "zod";
import type { RequestWithId } from "../types/index.js";

export function validateBody(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (err) {
      if (err instanceof ZodError) {
        const requestId = (req as RequestWithId).requestId || "unknown";
        res.status(400).json({
          error: "Validation failed",
          details: err.errors.map((e) => ({
            field: e.path.join("."),
            message: e.message,
          })),
          statusCode: 400,
          requestId,
        });
        return;
      }
      next(err);
    }
  };
}

export function validateQuery(schema: ZodSchema) {
  return (req: Request, res: Response, next: NextFunction): void => {
    try {
      req.query = schema.parse(req.query);
      next();
    } catch (err) {
      if (err instanceof ZodError) {
        const requestId = (req as RequestWithId).requestId || "unknown";
        res.status(400).json({
          error: "Query validation failed",
          details: err.errors.map((e) => ({
            field: e.path.join("."),
            message: e.message,
          })),
          statusCode: 400,
          requestId,
        });
        return;
      }
      next(err);
    }
  };
}

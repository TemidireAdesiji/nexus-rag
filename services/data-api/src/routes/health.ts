import { Router, Response } from "express";
import type { RequestWithId } from "../types/index.js";

const router = Router();

/**
 * @openapi
 * /ping:
 *   get:
 *     tags: [Health]
 *     summary: Health check endpoint
 *     description: Returns service health status
 *     responses:
 *       200:
 *         description: Service is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: operational
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 *                 uptime:
 *                   type: number
 */
router.get("/ping", (req: RequestWithId, res: Response) => {
  res.json({
    status: "operational",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    requestId: req.requestId,
  });
});

export default router;

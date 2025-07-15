import { Router, Response, NextFunction } from "express";
import { Consultation } from "../models/consultation.js";
import type { RequestWithId } from "../types/index.js";
import { logger } from "../utils/logger.js";

const router = Router();

/**
 * @openapi
 * /api/engagements:
 *   get:
 *     tags: [Consultations]
 *     summary: List all consultations
 *     description: Returns all consultation records with optional participant name filtering
 *     security:
 *       - BearerAuth: []
 *     parameters:
 *       - in: query
 *         name: name
 *         schema:
 *           type: string
 *         description: Filter by participant name (case-insensitive partial match)
 *     responses:
 *       200:
 *         description: List of consultations
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Consultation'
 *                 count:
 *                   type: integer
 *                 requestId:
 *                   type: string
 *       401:
 *         description: Unauthorized
 */
router.get(
  "/api/engagements",
  async (req: RequestWithId, res: Response, next: NextFunction) => {
    try {
      const nameFilter = req.query.name as string | undefined;
      const query = nameFilter
        ? { participants: { $regex: nameFilter, $options: "i" } }
        : {};

      const engagements = await Consultation.find(query)
        .sort({ scheduledDate: -1 })
        .lean();
      logger.debug("Fetched consultations", { count: engagements.length });

      res.json({
        data: engagements,
        count: engagements.length,
        requestId: req.requestId,
      });
    } catch (err) {
      next(err);
    }
  }
);

export default router;

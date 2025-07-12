import { Router, Response, NextFunction } from "express";
import { Sector } from "../models/sector.js";
import type { RequestWithId } from "../types/index.js";
import { logger } from "../utils/logger.js";

const router = Router();

/**
 * @openapi
 * /api/verticals:
 *   get:
 *     tags: [Sectors]
 *     summary: List all industry sectors
 *     description: Returns all tracked industry verticals with optional name filtering
 *     security:
 *       - BearerAuth: []
 *     parameters:
 *       - in: query
 *         name: sector
 *         schema:
 *           type: string
 *         description: Filter by sector name (case-insensitive partial match)
 *     responses:
 *       200:
 *         description: List of sectors
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Sector'
 *                 count:
 *                   type: integer
 *                 requestId:
 *                   type: string
 *       401:
 *         description: Unauthorized
 */
router.get(
  "/api/verticals",
  async (req: RequestWithId, res: Response, next: NextFunction) => {
    try {
      const sectorFilter = req.query.sector as string | undefined;
      const query = sectorFilter
        ? { verticalName: { $regex: sectorFilter, $options: "i" } }
        : {};

      const verticals = await Sector.find(query).lean();
      logger.debug("Fetched sectors", { count: verticals.length });

      res.json({
        data: verticals,
        count: verticals.length,
        requestId: req.requestId,
      });
    } catch (err) {
      next(err);
    }
  }
);

export default router;

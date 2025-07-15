import { Router, Response, NextFunction } from "express";
import { TeamMember } from "../models/team-member.js";
import type { RequestWithId, TeamAnalysis } from "../types/index.js";
import { logger } from "../utils/logger.js";

const router = Router();

/**
 * @openapi
 * /api/personnel:
 *   get:
 *     tags: [Team]
 *     summary: List all team members
 *     description: Returns all team members with optional name filtering
 *     security:
 *       - BearerAuth: []
 *     parameters:
 *       - in: query
 *         name: name
 *         schema:
 *           type: string
 *         description: Filter by team member name (case-insensitive partial match)
 *     responses:
 *       200:
 *         description: List of team members
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TeamMember'
 *                 count:
 *                   type: integer
 *                 requestId:
 *                   type: string
 *       401:
 *         description: Unauthorized
 */
router.get(
  "/api/personnel",
  async (req: RequestWithId, res: Response, next: NextFunction) => {
    try {
      const nameFilter = req.query.name as string | undefined;
      const query = nameFilter
        ? { fullName: { $regex: nameFilter, $options: "i" } }
        : {};

      const members = await TeamMember.find(query).lean();
      logger.debug("Fetched team members", { count: members.length });

      res.json({
        data: members,
        count: members.length,
        requestId: req.requestId,
      });
    } catch (err) {
      next(err);
    }
  }
);

/**
 * @openapi
 * /api/personnel/analysis:
 *   get:
 *     tags: [Team]
 *     summary: Team composition analysis
 *     description: Returns aggregated analysis of team composition including specialization distribution and title breakdown
 *     security:
 *       - BearerAuth: []
 *     responses:
 *       200:
 *         description: Team analysis data
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   $ref: '#/components/schemas/TeamAnalysis'
 *                 requestId:
 *                   type: string
 */
router.get(
  "/api/personnel/analysis",
  async (req: RequestWithId, res: Response, next: NextFunction) => {
    try {
      const members = await TeamMember.find().lean();

      const specializationDistribution: Record<string, number> = {};
      const titleBreakdown: Record<string, number> = {};

      for (const member of members) {
        const titleKey = member.title;
        titleBreakdown[titleKey] = (titleBreakdown[titleKey] || 0) + 1;

        for (const spec of member.specializations) {
          specializationDistribution[spec] =
            (specializationDistribution[spec] || 0) + 1;
        }
      }

      const analysis: TeamAnalysis = {
        totalMembers: members.length,
        specializationDistribution,
        titleBreakdown,
      };

      res.json({
        data: analysis,
        requestId: req.requestId,
      });
    } catch (err) {
      next(err);
    }
  }
);

export default router;

import { Router, Response, NextFunction } from "express";
import { Investment } from "../models/investment.js";
import type { RequestWithId, PortfolioAnalysis } from "../types/index.js";
import { logger } from "../utils/logger.js";

const router = Router();

/**
 * @openapi
 * /api/portfolio:
 *   get:
 *     tags: [Investments]
 *     summary: List all investments
 *     description: Returns all portfolio investments with optional company name filtering
 *     security:
 *       - BearerAuth: []
 *     parameters:
 *       - in: query
 *         name: company
 *         schema:
 *           type: string
 *         description: Filter by company name (case-insensitive partial match)
 *     responses:
 *       200:
 *         description: List of investments
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Investment'
 *                 count:
 *                   type: integer
 *                 requestId:
 *                   type: string
 *       401:
 *         description: Unauthorized
 */
router.get("/api/portfolio", async (req: RequestWithId, res: Response, next: NextFunction) => {
  try {
    const companyFilter = req.query.company as string | undefined;
    const query = companyFilter ? { companyName: { $regex: companyFilter, $options: "i" } } : {};

    const holdings = await Investment.find(query).lean();
    logger.debug("Fetched investments", { count: holdings.length });

    res.json({
      data: holdings,
      count: holdings.length,
      requestId: req.requestId,
    });
  } catch (err) {
    next(err);
  }
});

/**
 * @openapi
 * /api/portfolio/analysis:
 *   get:
 *     tags: [Investments]
 *     summary: Portfolio analysis and insights
 *     description: Returns aggregated portfolio analysis including capital deployment, status distribution, and sector exposure
 *     security:
 *       - BearerAuth: []
 *     responses:
 *       200:
 *         description: Portfolio analysis data
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   $ref: '#/components/schemas/PortfolioAnalysis'
 *                 requestId:
 *                   type: string
 */
router.get(
  "/api/portfolio/analysis",
  async (req: RequestWithId, res: Response, next: NextFunction) => {
    try {
      const holdings = await Investment.find().lean();

      const statusBreakdown: Record<string, number> = {};
      const assetClassDistribution: Record<string, number> = {};
      const sectorExposure: Record<string, number> = {};
      let totalCapitalDeployed = 0;

      for (const holding of holdings) {
        totalCapitalDeployed += holding.capitalDeployed;

        statusBreakdown[holding.currentStatus] = (statusBreakdown[holding.currentStatus] || 0) + 1;

        assetClassDistribution[holding.assetClass] =
          (assetClassDistribution[holding.assetClass] || 0) + 1;

        for (const sector of holding.sectors) {
          sectorExposure[sector] = (sectorExposure[sector] || 0) + 1;
        }
      }

      const analysis: PortfolioAnalysis = {
        totalInvestments: holdings.length,
        totalCapitalDeployed,
        averageInvestmentSize: holdings.length > 0 ? totalCapitalDeployed / holdings.length : 0,
        statusBreakdown,
        assetClassDistribution,
        sectorExposure,
      };

      res.json({
        data: analysis,
        requestId: req.requestId,
      });
    } catch (err) {
      next(err);
    }
  },
);

export default router;

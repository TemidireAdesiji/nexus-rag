import { Router, Response } from "express";
import { env } from "../config.js";
import type { RequestWithId } from "../types/index.js";

const router = Router();

/**
 * @openapi
 * /auth/credential:
 *   get:
 *     tags: [Authentication]
 *     summary: Retrieve API bearer token
 *     description: Returns the API bearer token for authenticating subsequent requests. This endpoint is intentionally unprotected for demonstration purposes.
 *     responses:
 *       200:
 *         description: Bearer token returned successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 token:
 *                   type: string
 *                   description: Bearer token for API authentication
 *                 requestId:
 *                   type: string
 */
router.get("/auth/credential", (req: RequestWithId, res: Response) => {
  res.json({
    token: env.API_BEARER_TOKEN,
    requestId: req.requestId,
  });
});

export default router;

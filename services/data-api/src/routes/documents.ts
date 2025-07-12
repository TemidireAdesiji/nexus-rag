import { Router, Response, NextFunction } from "express";
import path from "path";
import fs from "fs";
import archiver from "archiver";
import { env } from "../config.js";
import type { RequestWithId } from "../types/index.js";
import { logger } from "../utils/logger.js";

const router = Router();

/**
 * @openapi
 * /api/corpus/download:
 *   get:
 *     tags: [Documents]
 *     summary: Download document corpus
 *     description: Downloads all .txt files from the documents directory as a ZIP archive
 *     security:
 *       - BearerAuth: []
 *     responses:
 *       200:
 *         description: ZIP archive of all document files
 *         content:
 *           application/zip:
 *             schema:
 *               type: string
 *               format: binary
 *       404:
 *         description: No documents found
 *       401:
 *         description: Unauthorized
 */
router.get("/api/corpus/download", (req: RequestWithId, res: Response, next: NextFunction) => {
  try {
    const documentsPath = path.resolve(env.DOCUMENTS_DIR);

    if (!fs.existsSync(documentsPath)) {
      res.status(404).json({
        error: "Documents directory not found",
        statusCode: 404,
        requestId: req.requestId || "unknown",
      });
      return;
    }

    const textFiles = fs.readdirSync(documentsPath).filter((file) => file.endsWith(".txt"));

    if (textFiles.length === 0) {
      res.status(404).json({
        error: "No document files available",
        statusCode: 404,
        requestId: req.requestId || "unknown",
      });
      return;
    }

    logger.info("Preparing document corpus download", {
      fileCount: textFiles.length,
    });

    res.setHeader("Content-Type", "application/zip");
    res.setHeader("Content-Disposition", "attachment; filename=nexus-corpus.zip");

    const archive = archiver("zip", { zlib: { level: 9 } });

    archive.on("error", (err: Error) => {
      logger.error("Archive creation failed", { error: err.message });
      next(err);
    });

    archive.pipe(res);

    for (const file of textFiles) {
      const filePath = path.join(documentsPath, file);
      archive.file(filePath, { name: file });
    }

    void archive.finalize();
  } catch (err) {
    next(err);
  }
});

export default router;

import http from "http";
import { createApp } from "./app.js";
import { env } from "./config.js";
import { connectDatabase, disconnectDatabase } from "./db.js";
import { populateDatabase } from "./seed.js";
import { logger } from "./utils/logger.js";

logger.setLevel(env.LOG_LEVEL);

async function startServer(): Promise<void> {
  await connectDatabase();
  await populateDatabase();

  const app = createApp();
  const server = http.createServer(app);

  server.listen(env.PORT, () => {
    logger.info(`NexusRAG Data API running on port ${env.PORT}`, {
      environment: env.NODE_ENV,
      port: env.PORT,
    });
  });

  const shutdown = async (signal: string) => {
    logger.info(`Received ${signal}, initiating graceful shutdown`);

    server.close(async () => {
      logger.info("HTTP server closed");

      try {
        await disconnectDatabase();
        logger.info("Shutdown complete");
        process.exit(0);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        logger.error("Error during shutdown", { error: message });
        process.exit(1);
      }
    });

    setTimeout(() => {
      logger.error("Forced shutdown after timeout");
      process.exit(1);
    }, 10000);
  };

  process.on("SIGTERM", () => void shutdown("SIGTERM"));
  process.on("SIGINT", () => void shutdown("SIGINT"));
}

startServer().catch((err: unknown) => {
  const message = err instanceof Error ? err.message : String(err);
  logger.error("Failed to start server", { error: message });
  process.exit(1);
});

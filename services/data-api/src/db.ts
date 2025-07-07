import mongoose from "mongoose";
import { env } from "./config.js";
import { logger } from "./utils/logger.js";

export async function connectDatabase(): Promise<void> {
  try {
    await mongoose.connect(env.MONGODB_URI, {
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    });
    logger.info("Connected to MongoDB", {
      uri: env.MONGODB_URI.replace(/\/\/.*@/, "//<redacted>@"),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    logger.error("Failed to connect to MongoDB", { error: message });
    throw err;
  }
}

export async function disconnectDatabase(): Promise<void> {
  try {
    await mongoose.disconnect();
    logger.info("Disconnected from MongoDB");
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    logger.error("Error disconnecting from MongoDB", { error: message });
    throw err;
  }
}

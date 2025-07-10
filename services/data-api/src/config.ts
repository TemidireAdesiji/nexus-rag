import dotenv from "dotenv";
import { z } from "zod";

dotenv.config();

const envSchema = z.object({
  PORT: z.coerce.number().default(3456),
  MONGODB_URI: z.string().default("mongodb://localhost:27017/nexus_rag"),
  API_BEARER_TOKEN: z.string().min(1, "API_BEARER_TOKEN is required"),
  NODE_ENV: z
    .enum(["development", "production", "test"])
    .default("development"),
  CORS_ORIGINS: z.string().default("*"),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
  DOCUMENTS_DIR: z.string().default("./documents"),
});

type EnvConfig = z.infer<typeof envSchema>;

let _cached: EnvConfig | null = null;

export function getEnv(): EnvConfig {
  if (_cached) return _cached;
  const result = envSchema.safeParse(process.env);

  if (!result.success) {
    const formatted = result.error.flatten().fieldErrors;
    const messages = Object.entries(formatted)
      .map(([key, errs]) => `  ${key}: ${(errs ?? []).join(", ")}`)
      .join("\n");
    throw new Error(
      `Environment validation failed:\n${messages}`,
    );
  }

  _cached = result.data;
  return _cached;
}

/** Reset cached config — used in tests. */
export function resetEnv(): void {
  _cached = null;
}

export const env = new Proxy({} as EnvConfig, {
  get(_target, prop: string) {
    return getEnv()[prop as keyof EnvConfig];
  },
});

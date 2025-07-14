import { describe, it, expect, beforeAll, afterAll } from "vitest";
import request from "supertest";
import { resetEnv } from "../../src/config.js";
import { setupTestDatabase, teardownTestDatabase } from "../setup.js";
import type { Express } from "express";

const TEST_TOKEN = "test-nexus-token";
let app: Express;

beforeAll(async () => {
  process.env.API_BEARER_TOKEN = TEST_TOKEN;
  resetEnv();
  const { createApp } = await import("../../src/app.js");
  await setupTestDatabase();
  app = createApp();
}, 120_000);

afterAll(async () => {
  await teardownTestDatabase();
});

describe("GET /api/personnel", () => {
  it("should return 401 without authorization header", async () => {
    const res = await request(app).get("/api/personnel");
    expect(res.status).toBe(401);
    expect(res.body.error).toBeDefined();
  });

  it("should return 403 with invalid bearer token", async () => {
    const res = await request(app)
      .get("/api/personnel")
      .set("Authorization", "Bearer invalid-token-value");
    expect(res.status).toBe(403);
    expect(res.body.error).toContain("Invalid");
  });

  it("should return all team members with valid token", async () => {
    const res = await request(app)
      .get("/api/personnel")
      .set("Authorization", `Bearer ${TEST_TOKEN}`);
    expect(res.status).toBe(200);
    expect(res.body.data).toBeInstanceOf(Array);
    expect(res.body.count).toBe(5);
    expect(res.body.data[0]).toHaveProperty("fullName");
    expect(res.body.data[0]).toHaveProperty("title");
    expect(res.body.data[0]).toHaveProperty("biography");
    expect(res.body.data[0]).toHaveProperty("specializations");
  });

  it("should filter team members by name query parameter", async () => {
    const res = await request(app)
      .get("/api/personnel?name=Priya")
      .set("Authorization", `Bearer ${TEST_TOKEN}`);
    expect(res.status).toBe(200);
    expect(res.body.count).toBe(1);
    expect(res.body.data[0].fullName).toContain("Priya");
  });

  it("should return empty array when name filter matches nothing", async () => {
    const res = await request(app)
      .get("/api/personnel?name=NonexistentPerson")
      .set("Authorization", `Bearer ${TEST_TOKEN}`);
    expect(res.status).toBe(200);
    expect(res.body.count).toBe(0);
    expect(res.body.data).toEqual([]);
  });

  it("should include requestId in response", async () => {
    const res = await request(app)
      .get("/api/personnel")
      .set("Authorization", `Bearer ${TEST_TOKEN}`)
      .set("X-Request-ID", "test-req-123");
    expect(res.status).toBe(200);
    expect(res.body.requestId).toBe("test-req-123");
    expect(res.headers["x-request-id"]).toBe("test-req-123");
  });
});

describe("GET /api/personnel/analysis", () => {
  it("should return team analysis data", async () => {
    const res = await request(app)
      .get("/api/personnel/analysis")
      .set("Authorization", `Bearer ${TEST_TOKEN}`);
    expect(res.status).toBe(200);
    expect(res.body.data.totalMembers).toBe(5);
    expect(res.body.data.specializationDistribution).toBeDefined();
    expect(res.body.data.titleBreakdown).toBeDefined();
    expect(
      Object.keys(res.body.data.specializationDistribution).length
    ).toBeGreaterThan(0);
  });
});

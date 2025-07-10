import express from "express";
import cors from "cors";
import helmet from "helmet";
import swaggerJsdoc from "swagger-jsdoc";
import swaggerUi from "swagger-ui-express";
import { env } from "./config.js";
import { requestIdMiddleware } from "./middleware/request-id.js";
import { authMiddleware } from "./middleware/auth.js";
import { errorHandler } from "./middleware/error-handler.js";
import healthRouter from "./routes/health.js";
import authRouter from "./routes/auth.js";
import teamRouter from "./routes/team.js";
import investmentsRouter from "./routes/investments.js";
import sectorsRouter from "./routes/sectors.js";
import consultationsRouter from "./routes/consultations.js";
import documentsRouter from "./routes/documents.js";

const swaggerOptions: swaggerJsdoc.Options = {
  definition: {
    openapi: "3.0.3",
    info: {
      title: "NexusRAG Data API",
      version: "1.0.0",
      description:
        "REST API for NexusRAG portfolio data, team profiles, sector intelligence, and document corpus management.",
    },
    servers: [
      {
        url: `http://localhost:${env.PORT}`,
        description: "Local development server",
      },
    ],
    components: {
      securitySchemes: {
        BearerAuth: {
          type: "http",
          scheme: "bearer",
          bearerFormat: "token",
        },
      },
      schemas: {
        TeamMember: {
          type: "object",
          properties: {
            id: { type: "string" },
            fullName: { type: "string" },
            title: { type: "string" },
            biography: { type: "string" },
            specializations: {
              type: "array",
              items: { type: "string" },
            },
          },
        },
        Investment: {
          type: "object",
          properties: {
            id: { type: "string" },
            companyName: { type: "string" },
            assetClass: { type: "string" },
            capitalDeployed: { type: "number" },
            executionDate: { type: "string", format: "date-time" },
            currentStatus: { type: "string" },
            sectors: {
              type: "array",
              items: { type: "string" },
            },
          },
        },
        Sector: {
          type: "object",
          properties: {
            id: { type: "string" },
            verticalName: { type: "string" },
            overview: { type: "string" },
            emergingTrends: {
              type: "array",
              items: { type: "string" },
            },
            investmentTeam: {
              type: "array",
              items: { type: "string" },
            },
          },
        },
        Consultation: {
          type: "object",
          properties: {
            id: { type: "string" },
            subject: { type: "string" },
            scheduledDate: { type: "string", format: "date-time" },
            participants: {
              type: "array",
              items: { type: "string" },
            },
            synopsis: { type: "string" },
          },
        },
        TeamAnalysis: {
          type: "object",
          properties: {
            totalMembers: { type: "integer" },
            specializationDistribution: {
              type: "object",
              additionalProperties: { type: "integer" },
            },
            titleBreakdown: {
              type: "object",
              additionalProperties: { type: "integer" },
            },
          },
        },
        PortfolioAnalysis: {
          type: "object",
          properties: {
            totalInvestments: { type: "integer" },
            totalCapitalDeployed: { type: "number" },
            averageInvestmentSize: { type: "number" },
            statusBreakdown: {
              type: "object",
              additionalProperties: { type: "integer" },
            },
            assetClassDistribution: {
              type: "object",
              additionalProperties: { type: "integer" },
            },
            sectorExposure: {
              type: "object",
              additionalProperties: { type: "integer" },
            },
          },
        },
      },
    },
  },
  apis: ["./src/routes/*.ts", "./dist/routes/*.js"],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);

export function createApp(): express.Application {
  const app = express();

  const corsOrigins =
    env.CORS_ORIGINS === "*" ? "*" : env.CORS_ORIGINS.split(",").map((o) => o.trim());

  app.use(helmet());
  app.use(cors({ origin: corsOrigins }));
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  app.use(requestIdMiddleware);

  app.use(healthRouter);
  app.use(authRouter);

  app.use("/docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));
  app.get("/swagger.json", (_req, res) => {
    res.json(swaggerSpec);
  });

  app.use(authMiddleware);

  app.use(teamRouter);
  app.use(investmentsRouter);
  app.use(sectorsRouter);
  app.use(consultationsRouter);
  app.use(documentsRouter);

  app.use(errorHandler);

  return app;
}

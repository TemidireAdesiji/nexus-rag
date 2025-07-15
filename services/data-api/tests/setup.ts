import mongoose from "mongoose";
import { MongoMemoryServer } from "mongodb-memory-server";
import { TeamMember } from "../src/models/team-member.js";
import { Investment } from "../src/models/investment.js";
import { Sector } from "../src/models/sector.js";
import { Consultation } from "../src/models/consultation.js";
import { teamMembers, investments, sectors, consultations } from "../src/data/seed-data.js";

let mongoServer: MongoMemoryServer;

export async function setupTestDatabase(): Promise<void> {
  mongoServer = await MongoMemoryServer.create();
  const uri = mongoServer.getUri();
  await mongoose.connect(uri);

  await TeamMember.insertMany(teamMembers);
  await Investment.insertMany(investments);
  await Sector.insertMany(sectors);
  await Consultation.insertMany(consultations);
}

export async function teardownTestDatabase(): Promise<void> {
  await mongoose.disconnect();
  if (mongoServer) {
    await mongoServer.stop();
  }
}

export async function clearCollections(): Promise<void> {
  await TeamMember.deleteMany({});
  await Investment.deleteMany({});
  await Sector.deleteMany({});
  await Consultation.deleteMany({});
}

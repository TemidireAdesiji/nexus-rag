import { TeamMember } from "./models/team-member.js";
import { Investment } from "./models/investment.js";
import { Sector } from "./models/sector.js";
import { Consultation } from "./models/consultation.js";
import { teamMembers, investments, sectors, consultations } from "./data/seed-data.js";
import { logger } from "./utils/logger.js";

async function seedCollection<T>(
  model: { countDocuments: () => Promise<number>; insertMany: (docs: T[]) => Promise<unknown> },
  data: T[],
  label: string,
): Promise<void> {
  const existingCount = await model.countDocuments();
  if (existingCount === 0) {
    await model.insertMany(data);
    logger.info(`Seeded ${data.length} ${label}`);
  } else {
    logger.debug(`Skipping ${label} seed — ${existingCount} records exist`);
  }
}

export async function populateDatabase(): Promise<void> {
  await seedCollection(TeamMember, teamMembers, "team members");
  await seedCollection(Investment, investments, "investments");
  await seedCollection(Sector, sectors, "sectors");
  await seedCollection(Consultation, consultations, "consultations");
}

import mongoose, { Schema, Document } from "mongoose";

export interface ISector extends Document {
  id: string;
  verticalName: string;
  overview: string;
  emergingTrends: string[];
  investmentTeam: string[];
}

const sectorSchema = new Schema<ISector>(
  {
    id: { type: String, required: true, unique: true },
    verticalName: { type: String, required: true },
    overview: { type: String, required: true },
    emergingTrends: { type: [String], required: true, default: [] },
    investmentTeam: { type: [String], required: true, default: [] },
  },
  {
    timestamps: true,
    toJSON: {
      transform(_doc, ret: Record<string, unknown>) {
        delete ret._id;
        delete ret.__v;
        return ret;
      },
    },
  }
);

export const Sector = mongoose.model<ISector>("Sector", sectorSchema);

import mongoose, { Schema, Document } from "mongoose";

export interface IInvestment extends Document {
  id: string;
  companyName: string;
  assetClass: string;
  capitalDeployed: number;
  executionDate: Date;
  currentStatus: string;
  sectors: string[];
}

const investmentSchema = new Schema<IInvestment>(
  {
    id: { type: String, required: true, unique: true },
    companyName: { type: String, required: true },
    assetClass: { type: String, required: true },
    capitalDeployed: { type: Number, required: true },
    executionDate: { type: Date, required: true },
    currentStatus: { type: String, required: true },
    sectors: { type: [String], required: true, default: [] },
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

export const Investment = mongoose.model<IInvestment>(
  "Investment",
  investmentSchema
);

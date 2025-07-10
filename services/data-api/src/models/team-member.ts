import mongoose, { Schema, Document } from "mongoose";

export interface ITeamMember extends Document {
  id: string;
  fullName: string;
  title: string;
  biography: string;
  specializations: string[];
}

const teamMemberSchema = new Schema<ITeamMember>(
  {
    id: { type: String, required: true, unique: true },
    fullName: { type: String, required: true },
    title: { type: String, required: true },
    biography: { type: String, required: true },
    specializations: { type: [String], required: true, default: [] },
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

export const TeamMember = mongoose.model<ITeamMember>(
  "TeamMember",
  teamMemberSchema
);

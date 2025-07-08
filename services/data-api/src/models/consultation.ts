import mongoose, { Schema, Document } from "mongoose";

export interface IConsultation extends Document {
  id: string;
  subject: string;
  scheduledDate: Date;
  participants: string[];
  synopsis: string;
}

const consultationSchema = new Schema<IConsultation>(
  {
    id: { type: String, required: true, unique: true },
    subject: { type: String, required: true },
    scheduledDate: { type: Date, required: true },
    participants: { type: [String], required: true, default: [] },
    synopsis: { type: String, required: true },
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

export const Consultation = mongoose.model<IConsultation>(
  "Consultation",
  consultationSchema
);

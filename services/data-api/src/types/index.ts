import type { Request } from "express";

export interface TeamMemberDocument {
  id: string;
  fullName: string;
  title: string;
  biography: string;
  specializations: string[];
}

export interface InvestmentDocument {
  id: string;
  companyName: string;
  assetClass: string;
  capitalDeployed: number;
  executionDate: Date;
  currentStatus: string;
  sectors: string[];
}

export interface SectorDocument {
  id: string;
  verticalName: string;
  overview: string;
  emergingTrends: string[];
  investmentTeam: string[];
}

export interface ConsultationDocument {
  id: string;
  subject: string;
  scheduledDate: Date;
  participants: string[];
  synopsis: string;
}

export interface ApiErrorResponse {
  error: string;
  statusCode: number;
  requestId: string;
}

export interface ApiSuccessResponse<T> {
  data: T;
  count?: number;
  requestId: string;
}

export interface RequestWithId extends Request {
  requestId?: string;
}

export interface TeamAnalysis {
  totalMembers: number;
  specializationDistribution: Record<string, number>;
  titleBreakdown: Record<string, number>;
}

export interface PortfolioAnalysis {
  totalInvestments: number;
  totalCapitalDeployed: number;
  averageInvestmentSize: number;
  statusBreakdown: Record<string, number>;
  assetClassDistribution: Record<string, number>;
  sectorExposure: Record<string, number>;
}

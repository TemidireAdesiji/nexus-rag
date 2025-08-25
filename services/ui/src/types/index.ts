export interface DocumentSource {
  origin: string;
  relevance: number;
  excerpt: string;
}

export interface TraceStep {
  tool: string;
  params: Record<string, unknown>;
  rationale: string;
  outcome: string;
  error?: string;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: DocumentSource[];
  traceSteps?: TraceStep[];
}

export interface InquiryResult {
  question: string;
  answer: string;
  strategy: string;
  documentCount: number;
  sources: DocumentSource[];
  apiKeys: string[];
  traceSteps: TraceStep[];
}

export interface WellnessReport {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  appName: string;
  environment: string;
  pipelineReady: boolean;
  backendReachable: boolean;
  activeSessions: number;
  cacheEntries: number;
}

export interface ConversationRecord {
  sessionId: string;
  createdAt: string;
  messageCount: number;
}

export interface ConversationDetail {
  createdAt: string;
  messages: ConversationMessage[];
}

export interface SearchMode {
  id: string;
  label: string;
  summary: string;
}

export interface PlatformDetails {
  appName: string;
  apiVersion: string;
  environment: string;
  llmModel: string;
  embeddingModel: string;
  rerankerModel: string;
  maxQueryLength: number;
  searchModes: SearchMode[];
  availableTools: string[];
}

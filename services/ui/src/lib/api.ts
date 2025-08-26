import axios, { AxiosError } from "axios";
import type {
  InquiryResult,
  SearchMode,
  ConversationRecord,
  ConversationDetail,
  WellnessReport,
  PlatformDetails,
} from "../types";

export class ApiError extends Error {
  public statusCode: number;
  public details: string;

  constructor(message: string, statusCode: number, details = "") {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.details = details;
  }
}

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  timeout: 60_000,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    const status = error.response?.status ?? 500;
    const detail =
      error.response?.data?.detail ??
      error.response?.data?.message ??
      error.message;
    throw new ApiError(detail, status);
  },
);

export async function submitInquiry(
  question: string,
  strategy: string,
  sessionId: string,
): Promise<InquiryResult> {
  const { data } = await client.post<InquiryResult>("/query", {
    question,
    strategy,
    session_id: sessionId,
  });
  return data;
}

export async function fetchSearchModes(): Promise<SearchMode[]> {
  const { data } = await client.get<SearchMode[]>("/strategies");
  return data;
}

export async function openConversation(): Promise<{ sessionId: string }> {
  const { data } = await client.post<{ sessionId: string }>("/sessions");
  return data;
}

export async function loadConversation(
  id: string,
): Promise<ConversationDetail> {
  const { data } = await client.get<ConversationDetail>(`/sessions/${id}`);
  return data;
}

export async function closeConversation(id: string): Promise<void> {
  await client.delete(`/sessions/${id}`);
}

export async function listConversations(): Promise<ConversationRecord[]> {
  const { data } = await client.get<ConversationRecord[]>("/sessions");
  return data;
}

export async function checkWellness(): Promise<WellnessReport> {
  const { data } = await client.get<WellnessReport>("/health");
  return data;
}

export async function fetchPlatformDetails(): Promise<PlatformDetails> {
  const { data } = await client.get<PlatformDetails>("/info");
  return data;
}

export async function fetchAvailableTools(): Promise<string[]> {
  const { data } = await client.get<string[]>("/tools");
  return data;
}

export async function ingestDocument(file: File): Promise<{ message: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<{ message: string }>(
    "/ingest",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

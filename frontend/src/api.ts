import type { ReportAnalysisResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function analyzeReport(
  file: File,
  options: { includeAi: boolean }
): Promise<ReportAnalysisResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const endpoint = options.includeAi ? "/api/reports/analyze/ai" : "/api/reports/analyze";
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail || `请求失败：${response.status}`);
  }

  return response.json() as Promise<ReportAnalysisResponse>;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return typeof body.detail === "string" ? body.detail : "";
  } catch {
    return "";
  }
}

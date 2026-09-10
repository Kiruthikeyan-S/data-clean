import { ProcessResponse, BatchProcessResponse } from '../types';

const API_BASE = '/api';

export async function processFile(file: File): Promise<ProcessResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/process`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'File processing failed.';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = `Server returned status ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function processBatchFiles(files: File[]): Promise<BatchProcessResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE}/process-batch`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = 'Batch processing failed.';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = `Server returned status ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function getResult(id: string): Promise<ProcessResponse> {
  const response = await fetch(`${API_BASE}/result/${id}`);
  if (!response.ok) {
    throw new Error('Result not found or expired.');
  }
  return response.json();
}

export function getExportUrl(id: string, format: 'json' | 'csv' | 'excel'): string {
  return `${API_BASE}/export/${id}/${format}`;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

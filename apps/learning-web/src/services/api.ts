import type { StudyPlan, ProfileData, ProgressStats, PrerequisiteCheck, PlanEvaluation } from '../types';

const API_BASE = '/api';

export type AuthUser = {
  user_id: string;
  username: string;
};

export type AuthStatus = {
  auth_enabled: boolean;
  logged_in: boolean;
  user: AuthUser | null;
};

export type SSEEventHandlers = {
  onSessionCreated?: (sessionId: string) => void;
  onToken?: (text: string) => void;
  onProfile?: (profile: ProfileData) => void;
  onKnowledge?: (results: { success: boolean; results: unknown[]; count: number }) => void;
  onPrerequisite?: (check: PrerequisiteCheck) => void;
  onEvaluation?: (evaluation: PlanEvaluation) => void;
  onSchedule?: (schedule: { success: boolean; output_path: string }) => void;
  onPlan?: (plan: StudyPlan) => void;
  onDone?: (data: { plan_id: string; ics_path?: string }) => void;
  onError?: (error: { message: string }) => void;
};

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
  });
  if (!resp.ok) throw new Error(`API ${path} 返回 ${resp.status}`);
  return resp.json();
}

export async function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
  });
  if (!resp.ok) throw new Error(`API ${path} 返回 ${resp.status}`);
  return resp.json();
}

// ============ 认证相关 API ============

export async function authGetStatus(): Promise<AuthStatus> {
  return apiGet<AuthStatus>('/v1/auth/status');
}

export async function authLogin(username: string, password: string): Promise<{ status: string; user: AuthUser }> {
  return apiPost('/v1/auth/login', { username, password });
}

export async function authRegister(username: string, password: string): Promise<{ status: string; user: AuthUser }> {
  return apiPost('/v1/auth/register', { username, password });
}

export async function authLogout(): Promise<{ status: string }> {
  return apiPost('/v1/auth/logout', {});
}

export async function apiPostSSE(
  path: string,
  body: unknown,
  handlers: SSEEventHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    credentials: 'include',
    signal,
  });

  if (!resp.ok) {
    handlers.onError?.({ message: `请求失败: ${resp.status}` });
    return;
  }

  const reader = resp.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const event = JSON.parse(line.slice(6));
        const eventType = event.event;
        const data = event.data;

        switch (eventType) {
          case 'session_created':
            handlers.onSessionCreated?.(data.session_id);
            break;
          case 'token':
            handlers.onToken?.(data);
            break;
          case 'profile':
            handlers.onProfile?.(data);
            break;
          case 'knowledge':
            handlers.onKnowledge?.(data);
            break;
          case 'prerequisite':
            handlers.onPrerequisite?.(data);
            break;
          case 'evaluation':
            handlers.onEvaluation?.(data);
            break;
          case 'schedule':
            handlers.onSchedule?.(data);
            break;
          case 'plan':
            handlers.onPlan?.(data as StudyPlan);
            break;
          case 'done':
            handlers.onDone?.(data);
            break;
          case 'error':
            handlers.onError?.(data);
            break;
        }
      } catch {
        /* skip malformed */
      }
    }
  }
}

export function setApiBase(url: string) {
  (apiGet as unknown as { _base: string })._base = url;
}

export async function apiDeleteSession(sessionId: string): Promise<{ status: string }> {
  return apiDelete(`/v1/learn/session/${sessionId}`);
}

export async function apiDownloadICS(planId: string): Promise<void> {
  const resp = await fetch(`${API_BASE}/v1/learn/plan/${planId}/ics`, {
    credentials: 'include',
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`下载日历失败: ${resp.status} ${text}`);
  }
  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `study-plan-${planId}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

async function apiDelete<T = unknown>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`DELETE ${path} failed: ${resp.status} ${text}`);
  }
  return resp.json() as Promise<T>;
}

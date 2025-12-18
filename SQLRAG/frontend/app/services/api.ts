export interface User {
  id: number;
  name: string;
  email: string;
  role?: string;
}

export interface AuthResponse {
  token: string;
  role: string;
  user: User;
}

export interface ChatResponse {
  type: "message" | "approval_required";
  content?: string;
  message?: string;
  summary?: any;
  changes?: any[];
  interrupt_id?: string;
  approval_token?: string;
}

const API_Base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const authHeaders = (token?: string) => ({
  "Content-Type": "application/json",
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});

export async function login(email: string): Promise<AuthResponse> {
  const res = await fetch(`${API_Base}/auth/login`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

export async function sendMessage(threadId: string, message: string, token: string): Promise<ChatResponse> {
  const res = await fetch(`${API_Base}/chat`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ thread_id: threadId, message }),
  });
  if (!res.ok) throw new Error("Chat failed");
  return res.json();
}

export async function resumeChat(
  threadId: string,
  interruptId: string,
  approvalToken: string,
  approved: boolean,
  token: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_Base}/chat/resume`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      thread_id: threadId,
      interrupt_id: interruptId,
      approval_token: approvalToken,
      approved,
    }),
  });
  if (!res.ok) throw new Error("Resume failed");
  return res.json();
}

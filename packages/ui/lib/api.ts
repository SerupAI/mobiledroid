const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ProfileFingerprint {
  model: string;
  brand: string;
  manufacturer: string;
  build_fingerprint: string;
  android_version: string;
  sdk_version: string;
  hardware?: string;
  board?: string;
  product?: string;
  screen: {
    width: number;
    height: number;
    dpi: number;
  };
  timezone?: string;
  locale?: string;
}

export interface ProfileProxy {
  type: 'none' | 'http' | 'socks5';
  host: string | null;
  port: number | null;
  username: string | null;
  password: string | null;
}

export interface Profile {
  id: string;
  name: string;
  status: 'stopped' | 'starting' | 'running' | 'stopping' | 'error';
  container_id: string | null;
  adb_port: number | null;
  fingerprint: ProfileFingerprint;
  proxy: ProfileProxy;
  created_at: string;
  updated_at: string;
  last_started_at: string | null;
  last_stopped_at: string | null;
}

export interface ProfileCreate {
  name: string;
  fingerprint: ProfileFingerprint;
  proxy?: ProfileProxy;
}

export interface DeviceFingerprint {
  id: string;
  name: string;
  model: string;
  brand: string;
  manufacturer: string;
  build_fingerprint: string;
  android_version: string;
  sdk_version: string;
  screen: {
    width: number;
    height: number;
    dpi: number;
  };
}

export interface Task {
  id: string;
  profile_id: string;
  prompt: string;
  output_format: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  result: string | null;
  error_message: string | null;
  steps_taken: number;
  tokens_used: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Snapshot {
  id: string;
  name: string;
  description: string | null;
  profile_id: string;
  status: 'creating' | 'ready' | 'failed' | 'restoring';
  size_bytes: number | null;
  android_version: string;
  device_model: string;
  storage_path: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'step';
  content: string;
  step_number: number | null;
  action_type: string | null;
  action_reasoning: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cumulative_tokens: number | null;
  created_at: string;
}

export interface ChatSession {
  id: string;
  profile_id: string;
  initial_prompt: string;
  status: 'running' | 'completed' | 'error' | 'cancelled';
  total_tokens: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_steps: number;
  created_at: string;
  completed_at: string | null;
  messages: ChatMessage[];
}

export interface ChatSessionSummary {
  id: string;
  profile_id: string;
  initial_prompt: string;
  status: string;
  total_tokens: number;
  total_steps: number;
  created_at: string;
  completed_at: string | null;
  message_count: number;
}

export interface ChatHistoryResponse {
  sessions: ChatSessionSummary[];
  total_tokens: number;
  total_sessions: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // Profiles
  async getProfiles(): Promise<{ profiles: Profile[]; total: number }> {
    return this.request('/profiles');
  }

  async getProfile(id: string): Promise<Profile> {
    return this.request(`/profiles/${id}`);
  }

  async createProfile(data: ProfileCreate): Promise<Profile> {
    return this.request('/profiles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateProfile(
    id: string,
    data: Partial<ProfileCreate>
  ): Promise<Profile> {
    return this.request(`/profiles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteProfile(id: string): Promise<void> {
    return this.request(`/profiles/${id}`, {
      method: 'DELETE',
    });
  }

  async startProfile(id: string): Promise<Profile> {
    return this.request(`/profiles/${id}/start`, {
      method: 'POST',
    });
  }

  async stopProfile(id: string): Promise<Profile> {
    return this.request(`/profiles/${id}/stop`, {
      method: 'POST',
    });
  }

  getScreenshotUrl(id: string): string {
    return `${this.baseUrl}/profiles/${id}/screenshot`;
  }

  async checkDeviceReady(id: string): Promise<{
    profile_id: string;
    status: string;
    container_running: boolean;
    adb_connected: boolean;
    screen_available: boolean;
    ready: boolean;
    message: string;
  }> {
    return this.request(`/profiles/${id}/ready`);
  }

  async getDeviceInfo(id: string): Promise<Record<string, string>> {
    return this.request(`/profiles/${id}/device-info`);
  }

  // Fingerprints
  async getFingerprints(): Promise<{
    fingerprints: DeviceFingerprint[];
    total: number;
  }> {
    return this.request('/fingerprints');
  }

  async getFingerprint(id: string): Promise<DeviceFingerprint> {
    return this.request(`/fingerprints/${id}`);
  }

  // Device control
  async tap(
    profileId: string,
    x: number,
    y: number
  ): Promise<{ success: boolean }> {
    return this.request(`/devices/${profileId}/tap`, {
      method: 'POST',
      body: JSON.stringify({ x, y }),
    });
  }

  async swipe(
    profileId: string,
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    duration: number = 300
  ): Promise<{ success: boolean }> {
    return this.request(`/devices/${profileId}/swipe`, {
      method: 'POST',
      body: JSON.stringify({ x1, y1, x2, y2, duration }),
    });
  }

  async inputText(
    profileId: string,
    text: string
  ): Promise<{ success: boolean }> {
    return this.request(`/devices/${profileId}/type`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  async pressBack(profileId: string): Promise<{ success: boolean }> {
    return this.request(`/devices/${profileId}/back`, {
      method: 'POST',
    });
  }

  async pressHome(profileId: string): Promise<{ success: boolean }> {
    return this.request(`/devices/${profileId}/home`, {
      method: 'POST',
    });
  }

  // Tasks
  async getTasks(
    profileId: string
  ): Promise<{ tasks: Task[]; total: number }> {
    return this.request(`/tasks/profiles/${profileId}`);
  }

  async createTask(
    profileId: string,
    prompt: string,
    outputFormat?: string
  ): Promise<Task> {
    return this.request(`/tasks/profiles/${profileId}`, {
      method: 'POST',
      body: JSON.stringify({ prompt, output_format: outputFormat }),
    });
  }

  async executeTask(taskId: string): Promise<Task> {
    return this.request(`/tasks/${taskId}/execute`, {
      method: 'POST',
    });
  }

  async cancelTask(taskId: string): Promise<Task> {
    return this.request(`/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
  }

  // Snapshots
  async createSnapshot(
    profileId: string,
    name: string,
    description?: string
  ): Promise<Snapshot> {
    return this.request('/snapshots/', {
      method: 'POST',
      body: JSON.stringify({ profile_id: profileId, name, description }),
    });
  }

  async listSnapshots(profileId?: string): Promise<Snapshot[]> {
    const params = profileId ? `?profile_id=${profileId}` : '';
    return this.request(`/snapshots/${params}`);
  }

  async getSnapshot(snapshotId: string): Promise<Snapshot> {
    return this.request(`/snapshots/${snapshotId}`);
  }

  async restoreSnapshot(
    snapshotId: string,
    newProfileName?: string
  ): Promise<{ message: string; profile_id: string; profile_name: string }> {
    return this.request(`/snapshots/${snapshotId}/restore`, {
      method: 'POST',
      body: JSON.stringify({ new_profile_name: newProfileName }),
    });
  }

  async deleteSnapshot(snapshotId: string): Promise<{ message: string }> {
    return this.request(`/snapshots/${snapshotId}`, {
      method: 'DELETE',
    });
  }

  // Chat Sessions
  async getChatSession(sessionId: string): Promise<ChatSession> {
    return this.request(`/chat/sessions/${sessionId}`);
  }

  async getChatHistory(profileId: string): Promise<ChatHistoryResponse> {
    return this.request(`/chat/profiles/${profileId}/history`);
  }

  // Health
  async getHealth(): Promise<{ status: string; version: string }> {
    return this.request('/health');
  }
}

export const api = new ApiClient(API_URL);

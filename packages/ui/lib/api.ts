// Use relative /api path - Next.js rewrites proxy this to the backend
// This works regardless of what hostname/port the user accesses from
const API_BASE = '/api';

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
  status: 'pending' | 'scheduled' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  result: string | null;
  error_message: string | null;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  scheduled_at: string | null;
  max_retries: number;
  retry_count: number;
  queue_job_id: string | null;
  queued_at: string | null;
  steps_taken: number;
  tokens_used: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  chat_session_id: string | null;  // Link to chat session created during execution
}

export interface TaskCreate {
  prompt: string;
  output_format?: string | null;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  scheduled_at?: string | null;
  max_retries?: number;
  queue_immediately?: boolean;
}

export interface QueueStats {
  queued_jobs: number;
  task_counts: Record<string, number>;
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
  status: 'running' | 'completed' | 'error' | 'cancelled' | 'awaiting_approval';
  total_tokens: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_steps: number;
  max_steps_limit: number;
  require_approval: boolean;
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

// App Install types
export interface AppInfo {
  id: string;
  package: string;
  name: string;
  category: string;
}

export interface AppListResponse {
  apps: AppInfo[];
  total: number;
}

export interface AppBundle {
  id: string;
  name: string;
  description: string;
  apps: string[];
  app_count: number;
}

export interface BundleListResponse {
  bundles: AppBundle[];
  total: number;
}

export interface BundleDetailResponse {
  id: string;
  name: string;
  description: string;
  apps: AppInfo[];
}

export interface InstalledApp {
  id: string;
  package: string;
  name: string;
  category: string;
  installed: boolean;
}

export interface InstalledAppsResponse {
  apps: InstalledApp[];
  total: number;
}

export interface AppInstallResult {
  success: boolean;
  app: string | null;
  package: string | null;
  already_installed: boolean;
  installed: boolean;
  install_initiated: boolean;
  error: string | null;
}

export interface BundleInstallResult {
  success: boolean;
  bundle: string;
  apps: Array<{
    app_id: string;
    success: boolean;
    already_installed?: boolean;
    error?: string;
  }>;
  success_count: number;
  fail_count: number;
  skip_count: number;
}

export interface AppLaunchResult {
  success: boolean;
  app_id: string;
  package: string | null;
  error: string | null;
}

export interface AuroraStatus {
  installed: boolean;
  package: string;
}

// Proxy types
export interface Proxy {
  id: number;
  protocol: string;
  host: string;
  port: number;
  username: string | null;
  password: string | null;
  name: string | null;
  country: string | null;
  is_active: boolean;
  last_used_at: string | null;
  times_used: number;
  is_working: boolean | null;
  created_at: string;
  updated_at: string;
}

export interface ProxyCreate {
  protocol?: string;
  host: string;
  port: number;
  username?: string | null;
  password?: string | null;
  name?: string | null;
  country?: string | null;
}

export interface ProxyUploadResponse {
  imported: number;
  skipped: number;
  errors: string[];
}

// Settings types
export interface LLMProvider {
  id: string;
  name: string;
  display_name: string;
  base_url: string;
  has_api_key: boolean;
  api_key_masked: string | null;
  active: boolean;
  description: string | null;
  max_requests_per_minute: number | null;
  max_tokens_per_minute: number | null;
  created_at: string;
  updated_at: string;
}

export interface LLMProviderUpdate {
  api_key?: string | null;
  active?: boolean;
  max_requests_per_minute?: number | null;
  max_tokens_per_minute?: number | null;
}

export interface LLMModel {
  id: string;
  provider_id: string;
  name: string;
  display_name: string;
  description: string | null;
  context_window: number | null;
  max_output_tokens: number | null;
  input_cost_per_1k: number | null;
  output_cost_per_1k: number | null;
  supports_vision: boolean;
  supports_function_calling: boolean;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Integration {
  id: string;
  purpose: string;
  provider_id: string;
  provider_name: string;
  model_id: string;
  model_name: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SettingsStatus {
  providers: Record<string, {
    display_name: string;
    has_api_key: boolean;
    active: boolean;
  }>;
  ready_integrations: string[];
  missing_integrations: Array<{
    purpose: string;
    reason: string;
  }>;
  fully_configured: boolean;
}

class ApiClient {
  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
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

  async updateProfileProxy(
    id: string,
    proxy: ProfileProxy
  ): Promise<Profile> {
    return this.request(`/profiles/${id}/proxy`, {
      method: 'PATCH',
      body: JSON.stringify(proxy),
    });
  }

  getScreenshotUrl(id: string): string {
    return `${API_BASE}/profiles/${id}/screenshot`;
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

  async pasteText(
    profileId: string,
    text: string
  ): Promise<{ success: boolean; message?: string }> {
    return this.request(`/devices/${profileId}/paste`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  async getClipboard(
    profileId: string
  ): Promise<{ success: boolean; data?: { content: string | null } }> {
    return this.request(`/devices/${profileId}/clipboard`);
  }

  // Tasks
  async getTasks(
    profileId: string,
    status?: string
  ): Promise<{ tasks: Task[]; total: number }> {
    const params = status ? `?status=${status}` : '';
    return this.request(`/tasks/profiles/${profileId}${params}`);
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request(`/tasks/${taskId}`);
  }

  async createTask(
    profileId: string,
    data: TaskCreate
  ): Promise<Task> {
    return this.request(`/tasks/profiles/${profileId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async queueTask(taskId: string): Promise<Task> {
    return this.request(`/tasks/${taskId}/queue`, {
      method: 'POST',
    });
  }

  async cancelTask(taskId: string): Promise<Task> {
    return this.request(`/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
  }

  async retryTask(taskId: string): Promise<Task> {
    return this.request(`/tasks/${taskId}/retry`, {
      method: 'POST',
    });
  }

  async deleteTask(taskId: string): Promise<void> {
    return this.request(`/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  async getQueueStats(): Promise<QueueStats> {
    return this.request('/tasks/queue/stats');
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

  async continueSession(sessionId: string, additionalSteps: number = 10): Promise<{ message: string; session_id: string; new_max_steps: number }> {
    return this.request(`/chat/sessions/${sessionId}/continue`, {
      method: 'POST',
      body: JSON.stringify({ additional_steps: additionalSteps }),
    });
  }

  async cancelSession(sessionId: string): Promise<{ message: string; session_id: string }> {
    return this.request(`/chat/sessions/${sessionId}/cancel`, {
      method: 'POST',
    });
  }

  // App Install
  async getAvailableApps(category?: string): Promise<AppListResponse> {
    const params = category ? `?category=${category}` : '';
    return this.request(`/apps${params}`);
  }

  async getAppBundles(): Promise<BundleListResponse> {
    return this.request('/apps/bundles');
  }

  async getBundleDetail(bundleId: string): Promise<BundleDetailResponse> {
    return this.request(`/apps/bundles/${bundleId}`);
  }

  async getInstalledApps(profileId: string): Promise<InstalledAppsResponse> {
    return this.request(`/apps/profiles/${profileId}/installed`);
  }

  async checkAuroraStatus(profileId: string): Promise<AuroraStatus> {
    return this.request(`/apps/profiles/${profileId}/aurora/status`);
  }

  async installApp(
    profileId: string,
    appId: string,
    options?: { wait_for_install?: boolean; timeout?: number }
  ): Promise<AppInstallResult> {
    return this.request(`/apps/profiles/${profileId}/install/${appId}`, {
      method: 'POST',
      body: options ? JSON.stringify(options) : undefined,
    });
  }

  async installBundle(
    profileId: string,
    bundleId: string,
    options?: { sequential?: boolean }
  ): Promise<BundleInstallResult> {
    return this.request(`/apps/profiles/${profileId}/install/bundle/${bundleId}`, {
      method: 'POST',
      body: options ? JSON.stringify(options) : undefined,
    });
  }

  async launchApp(profileId: string, appId: string): Promise<AppLaunchResult> {
    return this.request(`/apps/profiles/${profileId}/launch/${appId}`, {
      method: 'POST',
    });
  }

  async openAppInAurora(profileId: string, appId: string): Promise<{ success: boolean; message: string; app_id: string }> {
    return this.request(`/apps/profiles/${profileId}/open-aurora/${appId}`, {
      method: 'POST',
    });
  }

  // Health
  async getHealth(): Promise<{ status: string; version: string }> {
    return this.request('/health');
  }

  // Settings - Providers
  async getProviders(): Promise<{ providers: LLMProvider[]; total: number }> {
    return this.request('/settings/providers');
  }

  async getProvider(providerId: string): Promise<LLMProvider> {
    return this.request(`/settings/providers/${providerId}`);
  }

  async updateProvider(
    providerId: string,
    data: LLMProviderUpdate
  ): Promise<LLMProvider> {
    return this.request(`/settings/providers/${providerId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Settings - Models
  async getModels(providerId?: string): Promise<{ models: LLMModel[]; total: number }> {
    const params = providerId ? `?provider_id=${providerId}` : '';
    return this.request(`/settings/models${params}`);
  }

  async getModel(modelId: string): Promise<LLMModel> {
    return this.request(`/settings/models/${modelId}`);
  }

  // Settings - Integrations
  async getIntegrations(): Promise<{ integrations: Integration[]; total: number }> {
    return this.request('/settings/integrations');
  }

  async updateIntegration(
    integrationId: string,
    data: { model_id?: string; active?: boolean }
  ): Promise<Integration> {
    return this.request(`/settings/integrations/${integrationId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Settings - Status
  async getSettingsStatus(): Promise<SettingsStatus> {
    return this.request('/settings/status');
  }

  // Proxies
  async getProxies(activeOnly: boolean = false): Promise<{ proxies: Proxy[]; total: number }> {
    const params = activeOnly ? '?active_only=true' : '';
    return this.request(`/proxies${params}`);
  }

  async getProxy(proxyId: number): Promise<Proxy> {
    return this.request(`/proxies/${proxyId}`);
  }

  async createProxy(data: ProxyCreate): Promise<Proxy> {
    return this.request('/proxies', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async uploadProxies(file: File): Promise<ProxyUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/proxies/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Upload failed: ${response.status}`);
    }

    return response.json();
  }

  async updateProxy(proxyId: number, data: Partial<ProxyCreate & { is_active?: boolean }>): Promise<Proxy> {
    return this.request(`/proxies/${proxyId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteProxy(proxyId: number): Promise<void> {
    return this.request(`/proxies/${proxyId}`, {
      method: 'DELETE',
    });
  }

  async deleteAllProxies(): Promise<{ deleted: number }> {
    return this.request('/proxies?confirm=true', {
      method: 'DELETE',
    });
  }
}

export const api = new ApiClient();

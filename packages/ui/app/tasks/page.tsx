'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Loader2,
  RefreshCw,
  Play,
  Square,
  RotateCcw,
  Trash2,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Timer,
  Zap,
  ChevronDown,
  ChevronUp,
  Filter,
  Plus,
  X,
  ExternalLink,
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, Task, QueueStats, Profile, TaskCreate } from '@/lib/api';
import { cn } from '@/lib/utils';
import Link from 'next/link';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-500/20 text-gray-400 border-gray-600',
  scheduled: 'bg-blue-500/20 text-blue-400 border-blue-600',
  queued: 'bg-yellow-500/20 text-yellow-400 border-yellow-600',
  running: 'bg-orange-500/20 text-orange-400 border-orange-600',
  completed: 'bg-green-500/20 text-green-400 border-green-600',
  failed: 'bg-red-500/20 text-red-400 border-red-600',
  cancelled: 'bg-gray-500/20 text-gray-500 border-gray-700',
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-600/50 text-gray-300',
  normal: 'bg-blue-600/50 text-blue-300',
  high: 'bg-orange-600/50 text-orange-300',
  urgent: 'bg-red-600/50 text-red-300',
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4" />,
  scheduled: <Timer className="h-4 w-4" />,
  queued: <Zap className="h-4 w-4" />,
  running: <Loader2 className="h-4 w-4 animate-spin" />,
  completed: <CheckCircle2 className="h-4 w-4" />,
  failed: <XCircle className="h-4 w-4" />,
  cancelled: <AlertCircle className="h-4 w-4" />,
};

function TaskCard({
  task,
  profile,
  onQueue,
  onCancel,
  onRetry,
  onDelete,
}: {
  task: Task;
  profile?: Profile;
  onQueue: () => void;
  onCancel: () => void;
  onRetry: () => void;
  onDelete: () => void;
}) {
  const [expanded, setExpanded] = useState(false);

  const canQueue = task.status === 'pending' || task.status === 'scheduled';
  const canCancel = ['pending', 'scheduled', 'queued', 'running'].includes(task.status);
  const canRetry = task.status === 'failed' && task.retry_count < task.max_retries;
  const canDelete = !['running'].includes(task.status);

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800 overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-gray-750"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={cn(
                  'inline-flex items-center gap-1.5 px-2 py-0.5 text-xs rounded border',
                  STATUS_COLORS[task.status]
                )}
              >
                {STATUS_ICONS[task.status]}
                {task.status}
              </span>
              <span
                className={cn(
                  'inline-flex px-2 py-0.5 text-xs rounded',
                  PRIORITY_COLORS[task.priority]
                )}
              >
                {task.priority}
              </span>
              {profile && (
                <span className="text-xs text-gray-500">
                  {profile.name}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-200 line-clamp-2">{task.prompt}</p>
            <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
              <span>Created: {new Date(task.created_at).toLocaleString()}</span>
              {task.steps_taken > 0 && <span>{task.steps_taken} steps</span>}
              {task.tokens_used > 0 && <span>{task.tokens_used.toLocaleString()} tokens</span>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {expanded ? (
              <ChevronUp className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            )}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-700 p-4 bg-gray-850">
          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            <div>
              <span className="text-gray-500">Task ID:</span>
              <span className="ml-2 font-mono text-xs">{task.id}</span>
            </div>
            <div>
              <span className="text-gray-500">Profile ID:</span>
              <span className="ml-2 font-mono text-xs">{task.profile_id}</span>
            </div>
            {task.scheduled_at && (
              <div>
                <span className="text-gray-500">Scheduled:</span>
                <span className="ml-2">{new Date(task.scheduled_at).toLocaleString()}</span>
              </div>
            )}
            {task.queued_at && (
              <div>
                <span className="text-gray-500">Queued:</span>
                <span className="ml-2">{new Date(task.queued_at).toLocaleString()}</span>
              </div>
            )}
            {task.started_at && (
              <div>
                <span className="text-gray-500">Started:</span>
                <span className="ml-2">{new Date(task.started_at).toLocaleString()}</span>
              </div>
            )}
            {task.completed_at && (
              <div>
                <span className="text-gray-500">Completed:</span>
                <span className="ml-2">{new Date(task.completed_at).toLocaleString()}</span>
              </div>
            )}
            <div>
              <span className="text-gray-500">Retries:</span>
              <span className="ml-2">{task.retry_count} / {task.max_retries}</span>
            </div>
            {task.queue_job_id && (
              <div>
                <span className="text-gray-500">Job ID:</span>
                <span className="ml-2 font-mono text-xs">{task.queue_job_id}</span>
              </div>
            )}
          </div>

          {task.result && (
            <div className="mb-4">
              <span className="text-gray-500 text-sm">Result:</span>
              <div className="mt-1 p-3 rounded bg-gray-900 text-sm text-gray-300 whitespace-pre-wrap">
                {task.result}
              </div>
            </div>
          )}

          {task.error_message && (
            <div className="mb-4">
              <span className="text-red-400 text-sm">Error:</span>
              <div className="mt-1 p-3 rounded bg-red-900/20 text-sm text-red-300 border border-red-800">
                {task.error_message}
              </div>
            </div>
          )}

          {task.chat_session_id && (
            <div className="mb-4">
              <Link
                href={`/history?session=${task.chat_session_id}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-purple-600/30 text-purple-300 rounded hover:bg-purple-600/50 border border-purple-600"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="h-3 w-3" />
                View Execution Log
              </Link>
            </div>
          )}

          <div className="flex items-center gap-2 pt-2 border-t border-gray-700">
            {canQueue && (
              <button
                onClick={(e) => { e.stopPropagation(); onQueue(); }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
              >
                <Play className="h-3 w-3" />
                Queue
              </button>
            )}
            {canCancel && (
              <button
                onClick={(e) => { e.stopPropagation(); onCancel(); }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-orange-600 text-white rounded hover:bg-orange-700"
              >
                <Square className="h-3 w-3" />
                Cancel
              </button>
            )}
            {canRetry && (
              <button
                onClick={(e) => { e.stopPropagation(); onRetry(); }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <RotateCcw className="h-3 w-3" />
                Retry
              </button>
            )}
            {canDelete && (
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(); }}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 ml-auto"
              >
                <Trash2 className="h-3 w-3" />
                Delete
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function CreateTaskForm({
  profiles,
  onClose,
  onSuccess,
}: {
  profiles: Profile[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [profileId, setProfileId] = useState('');
  const [prompt, setPrompt] = useState('');
  const [priority, setPriority] = useState<'low' | 'normal' | 'high' | 'urgent'>('normal');
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduledAt, setScheduledAt] = useState('');
  const [queueImmediately, setQueueImmediately] = useState(true);
  const [maxRetries, setMaxRetries] = useState(3);

  const runningProfiles = profiles.filter(p => p.status === 'running');

  const createMutation = useMutation({
    mutationFn: (data: TaskCreate) => api.createTask(profileId, data),
    onSuccess: () => {
      onSuccess();
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!profileId || !prompt.trim()) return;

    const data: TaskCreate = {
      prompt: prompt.trim(),
      priority,
      max_retries: maxRetries,
      queue_immediately: scheduleEnabled ? false : queueImmediately,
    };

    if (scheduleEnabled && scheduledAt) {
      data.scheduled_at = new Date(scheduledAt).toISOString();
      data.queue_immediately = false;
    }

    createMutation.mutate(data);
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg border border-gray-700 w-full max-w-lg">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold">Create New Task</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Profile selector */}
          <div>
            <label className="block text-sm font-medium mb-1">Device Profile</label>
            <select
              value={profileId}
              onChange={(e) => setProfileId(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white"
              required
            >
              <option value="">Select a profile...</option>
              {runningProfiles.length > 0 ? (
                runningProfiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name}
                  </option>
                ))
              ) : (
                <option disabled>No running profiles</option>
              )}
            </select>
            {runningProfiles.length === 0 && (
              <p className="text-xs text-yellow-400 mt-1">
                Start a profile first to create tasks
              </p>
            )}
          </div>

          {/* Prompt */}
          <div>
            <label className="block text-sm font-medium mb-1">Task Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe what the AI should do on the device..."
              rows={4}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white placeholder-gray-500 resize-none"
              required
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as typeof priority)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          {/* Schedule toggle */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="scheduleEnabled"
              checked={scheduleEnabled}
              onChange={(e) => setScheduleEnabled(e.target.checked)}
              className="rounded border-gray-600 bg-gray-900"
            />
            <label htmlFor="scheduleEnabled" className="text-sm">
              Schedule for later
            </label>
          </div>

          {/* Schedule datetime */}
          {scheduleEnabled && (
            <div>
              <label className="block text-sm font-medium mb-1">Scheduled Time</label>
              <input
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white"
                required={scheduleEnabled}
              />
            </div>
          )}

          {/* Queue immediately (only when not scheduled) */}
          {!scheduleEnabled && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="queueImmediately"
                checked={queueImmediately}
                onChange={(e) => setQueueImmediately(e.target.checked)}
                className="rounded border-gray-600 bg-gray-900"
              />
              <label htmlFor="queueImmediately" className="text-sm">
                Queue immediately (start execution right away)
              </label>
            </div>
          )}

          {/* Max retries */}
          <div>
            <label className="block text-sm font-medium mb-1">Max Retries</label>
            <input
              type="number"
              value={maxRetries}
              onChange={(e) => setMaxRetries(parseInt(e.target.value) || 0)}
              min={0}
              max={10}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white"
            />
          </div>

          {/* Error message */}
          {createMutation.error && (
            <div className="p-3 bg-red-900/20 border border-red-800 rounded text-red-300 text-sm">
              {createMutation.error.message}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm bg-gray-700 text-white rounded hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!profileId || !prompt.trim() || createMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Create Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function QueueStatsCard({ stats }: { stats: QueueStats }) {
  const totalTasks = Object.values(stats.task_counts).reduce((a, b) => a + b, 0);

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800 p-4">
      <h3 className="text-lg font-semibold mb-4">Queue Statistics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-3xl font-bold text-yellow-400">{stats.queued_jobs}</div>
          <div className="text-sm text-gray-400">In Queue</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-orange-400">{stats.task_counts.running || 0}</div>
          <div className="text-sm text-gray-400">Running</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-green-400">{stats.task_counts.completed || 0}</div>
          <div className="text-sm text-gray-400">Completed</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-red-400">{stats.task_counts.failed || 0}</div>
          <div className="text-sm text-gray-400">Failed</div>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.task_counts).map(([status, count]) => (
            <span
              key={status}
              className={cn(
                'inline-flex items-center gap-1.5 px-2 py-1 text-xs rounded border',
                STATUS_COLORS[status] || 'bg-gray-600 text-gray-300'
              )}
            >
              {status}: {count}
            </span>
          ))}
        </div>
        <div className="text-sm text-gray-500 mt-2">
          Total: {totalTasks} tasks
        </div>
      </div>
    </div>
  );
}

export default function TasksPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.getProfiles(),
  });

  const { data: queueStats, isLoading: statsLoading } = useQuery({
    queryKey: ['queueStats'],
    queryFn: () => api.getQueueStats(),
    refetchInterval: 5000,
  });

  // Fetch tasks for selected profile or all running profiles
  const profilesToQuery = selectedProfileId
    ? [selectedProfileId]
    : (profilesData?.profiles.filter(p => p.status === 'running').map(p => p.id) || []);

  const taskQueries = useQuery({
    queryKey: ['allTasks', profilesToQuery, statusFilter],
    queryFn: async () => {
      if (profilesToQuery.length === 0) {
        // If no running profiles, fetch from all profiles
        const allProfiles = profilesData?.profiles || [];
        const results = await Promise.all(
          allProfiles.map(p => api.getTasks(p.id, statusFilter || undefined))
        );
        return results.flatMap(r => r.tasks);
      }
      const results = await Promise.all(
        profilesToQuery.map(id => api.getTasks(id, statusFilter || undefined))
      );
      return results.flatMap(r => r.tasks);
    },
    enabled: !!profilesData,
    refetchInterval: 5000,
  });

  const queueMutation = useMutation({
    mutationFn: (taskId: string) => api.queueTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['allTasks'] });
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (taskId: string) => api.cancelTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['allTasks'] });
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: (taskId: string) => api.retryTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['allTasks'] });
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (taskId: string) => api.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['allTasks'] });
      queryClient.invalidateQueries({ queryKey: ['queueStats'] });
    },
  });

  const profiles = profilesData?.profiles || [];
  const tasks = taskQueries.data || [];

  // Sort tasks by created_at descending
  const sortedTasks = [...tasks].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ['allTasks'] });
    queryClient.invalidateQueries({ queryKey: ['queueStats'] });
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Task Queue</h1>
            <p className="text-gray-400">Manage and monitor scheduled tasks</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
            >
              <Plus className="h-4 w-4" />
              Create Task
            </button>
            <button
              onClick={refreshAll}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Create Task Modal */}
        {showCreateForm && (
          <CreateTaskForm
            profiles={profiles}
            onClose={() => setShowCreateForm(false)}
            onSuccess={() => {
              queryClient.invalidateQueries({ queryKey: ['allTasks'] });
              queryClient.invalidateQueries({ queryKey: ['queueStats'] });
            }}
          />
        )}

        {/* Queue Stats */}
        {statsLoading ? (
          <div className="rounded-lg border border-gray-700 bg-gray-800 p-8 text-center mb-6">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-gray-400" />
          </div>
        ) : queueStats ? (
          <div className="mb-6">
            <QueueStatsCard stats={queueStats} />
          </div>
        ) : null}

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-400">Filter:</span>
          </div>
          <select
            value={selectedProfileId}
            onChange={(e) => setSelectedProfileId(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white"
          >
            <option value="">All Profiles</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.name} ({profile.status})
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="scheduled">Scheduled</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {/* Tasks List */}
        {taskQueries.isLoading ? (
          <div className="rounded-lg border border-gray-700 bg-gray-800 p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-gray-400" />
            <p className="text-gray-400 mt-2">Loading tasks...</p>
          </div>
        ) : sortedTasks.length === 0 ? (
          <div className="rounded-lg border border-gray-700 bg-gray-800 p-8 text-center">
            <p className="text-gray-400">No tasks found</p>
            <p className="text-sm text-gray-500 mt-1">
              Create tasks from the profile page using AI Device Control
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedTasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                profile={profiles.find(p => p.id === task.profile_id)}
                onQueue={() => queueMutation.mutate(task.id)}
                onCancel={() => cancelMutation.mutate(task.id)}
                onRetry={() => retryMutation.mutate(task.id)}
                onDelete={() => deleteMutation.mutate(task.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Camera,
  RotateCcw,
  Trash2,
  Loader2,
  HardDrive,
  Calendar,
  ChevronRight,
} from 'lucide-react';
import { api, Snapshot } from '@/lib/api';

interface SnapshotListProps {
  profileId?: string;
  showProfileName?: boolean;
  compact?: boolean;
}

function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return '-';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleString();
}

export function SnapshotList({ profileId, showProfileName = false, compact = false }: SnapshotListProps) {
  const queryClient = useQueryClient();
  const [restoringId, setRestoringId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data: snapshots, isLoading } = useQuery({
    queryKey: ['snapshots', profileId],
    queryFn: () => api.listSnapshots(profileId),
  });

  const restoreMutation = useMutation({
    mutationFn: (snapshotId: string) => api.restoreSnapshot(snapshotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
      setRestoringId(null);
    },
    onError: (error: Error) => {
      alert(`Failed to restore: ${error.message}`);
      setRestoringId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (snapshotId: string) => api.deleteSnapshot(snapshotId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
      setDeletingId(null);
    },
    onError: (error: Error) => {
      alert(`Failed to delete: ${error.message}`);
      setDeletingId(null);
    },
  });

  const handleRestore = (snapshot: Snapshot) => {
    if (window.confirm(`Restore from "${snapshot.name}"? This will create a new device profile.`)) {
      setRestoringId(snapshot.id);
      restoreMutation.mutate(snapshot.id);
    }
  };

  const handleDelete = (snapshot: Snapshot) => {
    if (window.confirm(`Delete snapshot "${snapshot.name}"? This cannot be undone.`)) {
      setDeletingId(snapshot.id);
      deleteMutation.mutate(snapshot.id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="text-center py-8">
        <Camera className="mx-auto h-10 w-10 text-gray-600 mb-3" />
        <p className="text-gray-400 text-sm">No snapshots yet</p>
        <p className="text-gray-500 text-xs mt-1">
          Create a snapshot to save the device state
        </p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {snapshots.slice(0, 5).map((snapshot) => (
          <div
            key={snapshot.id}
            className="flex items-center justify-between p-2 bg-gray-800 rounded hover:bg-gray-750"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{snapshot.name}</p>
              <p className="text-xs text-gray-500">
                {formatDate(snapshot.created_at)} · {formatBytes(snapshot.size_bytes)}
              </p>
            </div>
            <div className="flex items-center gap-1 ml-2">
              <button
                onClick={() => handleRestore(snapshot)}
                disabled={restoringId === snapshot.id}
                className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded disabled:opacity-50"
                title="Restore"
              >
                {restoringId === snapshot.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RotateCcw className="h-4 w-4" />
                )}
              </button>
              <button
                onClick={() => handleDelete(snapshot)}
                disabled={deletingId === snapshot.id}
                className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded disabled:opacity-50"
                title="Delete"
              >
                {deletingId === snapshot.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        ))}
        {snapshots.length > 5 && (
          <a
            href="/snapshots"
            className="block text-center text-sm text-primary-400 hover:text-primary-300 py-2"
          >
            View all {snapshots.length} snapshots
          </a>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {snapshots.map((snapshot) => (
        <div
          key={snapshot.id}
          className="flex items-center justify-between p-4 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700"
        >
          <div className="flex items-center gap-4 flex-1 min-w-0">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-800">
              <Camera className="h-5 w-5 text-gray-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="font-medium truncate">{snapshot.name}</p>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  snapshot.status === 'ready' ? 'bg-green-900/50 text-green-400' :
                  snapshot.status === 'creating' ? 'bg-yellow-900/50 text-yellow-400' :
                  'bg-red-900/50 text-red-400'
                }`}>
                  {snapshot.status}
                </span>
              </div>
              {snapshot.description && (
                <p className="text-sm text-gray-400 truncate">{snapshot.description}</p>
              )}
              <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatDate(snapshot.created_at)}
                </span>
                <span className="flex items-center gap-1">
                  <HardDrive className="h-3 w-3" />
                  {formatBytes(snapshot.size_bytes)}
                </span>
                <span>{snapshot.device_model} · Android {snapshot.android_version}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={() => handleRestore(snapshot)}
              disabled={restoringId === snapshot.id || snapshot.status !== 'ready'}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Restore"
            >
              {restoringId === snapshot.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCcw className="h-4 w-4" />
              )}
              Restore
            </button>
            <button
              onClick={() => handleDelete(snapshot)}
              disabled={deletingId === snapshot.id}
              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-600/20 text-red-400 rounded hover:bg-red-600/30 disabled:opacity-50"
              title="Delete"
            >
              {deletingId === snapshot.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

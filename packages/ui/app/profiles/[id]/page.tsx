'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Square, Settings, Loader2, Camera } from 'lucide-react';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { DeviceViewerWS } from '@/components/DeviceViewerWS';
import { DeviceControls } from '@/components/DeviceControls';
import { DeviceChat } from '@/components/DeviceChat';
import { SnapshotList } from '@/components/SnapshotList';
import { CreateSnapshotModal } from '@/components/CreateSnapshotModal';
import { api } from '@/lib/api';
import { cn, getStatusColor } from '@/lib/utils';

export default function ProfilePage() {
  const params = useParams();
  const profileId = params.id as string;
  const queryClient = useQueryClient();
  const [showCreateSnapshot, setShowCreateSnapshot] = useState(false);

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['profile', profileId],
    queryFn: () => api.getProfile(profileId),
    refetchInterval: 10000, // Reduced from 3s to 10s
  });

  const { data: tasksData } = useQuery({
    queryKey: ['tasks', profileId],
    queryFn: () => api.getTasks(profileId),
    enabled: profile?.status === 'running',
    refetchInterval: 5000, // Reduced from 2s to 5s
  });

  const stopMutation = useMutation({
    mutationFn: () => api.stopProfile(profileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', profileId] });
    },
  });

  const tapMutation = useMutation({
    mutationFn: ({ x, y }: { x: number; y: number }) =>
      api.tap(profileId, x, y),
  });

  const handleTap = (x: number, y: number) => {
    tapMutation.mutate({ x, y });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-gray-950">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
            {error ? (error as Error).message : 'Profile not found'}
          </div>
        </main>
      </div>
    );
  }

  const tasks = tasksData?.tasks || [];

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="flex items-center justify-between mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gray-400 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>

          <div className="flex items-center gap-3">
            <span
              className={cn(
                'inline-flex items-center gap-1.5 text-sm',
                getStatusColor(profile.status)
              )}
            >
              <span className="relative flex h-2 w-2">
                {profile.status === 'running' && (
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                )}
                <span
                  className={cn(
                    'relative inline-flex h-2 w-2 rounded-full',
                    profile.status === 'running' && 'bg-green-500',
                    profile.status === 'stopped' && 'bg-gray-500'
                  )}
                />
              </span>
              {profile.status}
            </span>

            {profile.status === 'running' && (
              <button
                onClick={() => stopMutation.mutate()}
                disabled={stopMutation.isPending}
                className="flex items-center gap-2 rounded-md bg-red-600/20 px-3 py-1.5 text-sm text-red-400 hover:bg-red-600/30"
              >
                {stopMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Square className="h-4 w-4" />
                )}
                Stop
              </button>
            )}
          </div>
        </div>

        {/* Profile header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold">{profile.name}</h1>
          <p className="text-gray-400">
            {profile.fingerprint.brand} {profile.fingerprint.model} &bull;
            Android {profile.fingerprint.android_version}
          </p>
        </div>

        {profile.status === 'running' ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Device viewer */}
            <div>
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <DeviceViewerWS profileId={profileId} onTap={handleTap} />
                <div className="mt-4">
                  <DeviceControls profileId={profileId} />
                </div>
              </div>
            </div>

            {/* AI Chat panel */}
            <div className="space-y-6">
              <DeviceChat profileId={profileId} />

              {/* Task history */}
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <h2 className="font-semibold mb-4">Recent Tasks</h2>
                {tasks.length === 0 ? (
                  <p className="text-gray-500 text-sm">No tasks yet</p>
                ) : (
                  <div className="space-y-2">
                    {tasks.slice(0, 5).map((task) => (
                      <div
                        key={task.id}
                        className="rounded-lg border border-gray-700 bg-gray-800 p-3"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm line-clamp-2">{task.prompt}</p>
                          <span
                            className={cn(
                              'text-xs px-2 py-0.5 rounded',
                              task.status === 'completed' &&
                                'bg-green-500/20 text-green-400',
                              task.status === 'running' &&
                                'bg-yellow-500/20 text-yellow-400',
                              task.status === 'failed' &&
                                'bg-red-500/20 text-red-400',
                              task.status === 'pending' &&
                                'bg-gray-500/20 text-gray-400'
                            )}
                          >
                            {task.status}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {task.steps_taken} steps
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Device info */}
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <h2 className="font-semibold mb-4">Device Info</h2>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-500">Brand:</span>{' '}
                    {profile.fingerprint.brand}
                  </div>
                  <div>
                    <span className="text-gray-500">Model:</span>{' '}
                    {profile.fingerprint.model}
                  </div>
                  <div>
                    <span className="text-gray-500">Android:</span>{' '}
                    {profile.fingerprint.android_version}
                  </div>
                  <div>
                    <span className="text-gray-500">SDK:</span>{' '}
                    {profile.fingerprint.sdk_version}
                  </div>
                  <div>
                    <span className="text-gray-500">Screen:</span>{' '}
                    {profile.fingerprint.screen.width}x
                    {profile.fingerprint.screen.height}
                  </div>
                  <div>
                    <span className="text-gray-500">DPI:</span>{' '}
                    {profile.fingerprint.screen.dpi}
                  </div>
                  <div>
                    <span className="text-gray-500">Container ID:</span>{' '}
                    <span className="text-xs font-mono">{profile.container_id?.substring(0, 12) || '-'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">ADB Address:</span>{' '}
                    <span className="text-xs">mobiledroid-{profile.id}:5555</span>
                  </div>
                </div>
              </div>

              {/* Snapshots */}
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold">Snapshots</h2>
                  <button
                    onClick={() => setShowCreateSnapshot(true)}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700"
                  >
                    <Camera className="h-4 w-4" />
                    Create Snapshot
                  </button>
                </div>
                <SnapshotList profileId={profileId} compact />
              </div>
            </div>
          </div>

        ) : (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-4">
              Profile is not running. Start it to view and control the device.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-md bg-primary-600 px-4 py-2 text-white hover:bg-primary-700"
            >
              Go to Dashboard
            </Link>
          </div>
        )}

        {/* Create Snapshot Modal */}
        {showCreateSnapshot && (
          <CreateSnapshotModal
            profileId={profileId}
            profileName={profile.name}
            onClose={() => setShowCreateSnapshot(false)}
          />
        )}
      </main>
    </div>
  );
}

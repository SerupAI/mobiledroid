'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Play,
  Square,
  Trash2,
  Monitor,
  Smartphone,
  Loader2,
} from 'lucide-react';
import { api, Profile } from '@/lib/api';
import { cn, getStatusColor, getStatusBgColor } from '@/lib/utils';

interface ProfileCardProps {
  profile: Profile;
}

export function ProfileCard({ profile }: ProfileCardProps) {
  const queryClient = useQueryClient();
  const [isHovered, setIsHovered] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Track elapsed time while starting
  useEffect(() => {
    if (profile.status === 'starting') {
      if (!startTime) {
        setStartTime(Date.now());
      }
      const interval = setInterval(() => {
        if (startTime) {
          setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
        }
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setStartTime(null);
      setElapsedSeconds(0);
    }
  }, [profile.status, startTime]);

  // Poll for status updates while starting
  useEffect(() => {
    if (profile.status === 'starting') {
      const interval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['profiles'] });
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [profile.status, queryClient]);

  const startMutation = useMutation({
    mutationFn: () => api.startProfile(profile.id),
    onSuccess: () => {
      setStartTime(Date.now());
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
    onError: (error: Error) => {
      alert(`Failed to start profile: ${error.message}`);
    },
  });

  const stopMutation = useMutation({
    mutationFn: () => api.stopProfile(profile.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
    onError: (error: Error) => {
      alert(`Failed to stop profile: ${error.message}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteProfile(profile.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
    onError: (error: Error) => {
      alert(`Failed to delete profile: ${error.message}`);
    },
  });

  const isLoading =
    startMutation.isPending ||
    stopMutation.isPending ||
    deleteMutation.isPending;
  const isRunning = profile.status === 'running';
  const isStarting = profile.status === 'starting';
  const isStopping = profile.status === 'stopping';

  const handleDelete = () => {
    if (window.confirm(`Delete profile "${profile.name}"?`)) {
      deleteMutation.mutate();
    }
  };

  return (
    <div
      className={cn(
        'relative rounded-lg border p-4 transition-all',
        getStatusBgColor(profile.status),
        isHovered && 'border-primary-500/50'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Status indicator */}
      <div className="absolute top-4 right-4">
        <span
          className={cn(
            'inline-flex items-center gap-1.5 text-xs font-medium',
            getStatusColor(profile.status)
          )}
        >
          <span className="relative flex h-2 w-2">
            {(isRunning || isStarting || isStopping) && (
              <span
                className={cn(
                  'absolute inline-flex h-full w-full animate-ping rounded-full opacity-75',
                  isRunning && 'bg-green-400',
                  isStarting && 'bg-yellow-400',
                  isStopping && 'bg-yellow-400'
                )}
              />
            )}
            <span
              className={cn(
                'relative inline-flex h-2 w-2 rounded-full',
                isRunning && 'bg-green-500',
                isStarting && 'bg-yellow-500',
                isStopping && 'bg-yellow-500',
                profile.status === 'stopped' && 'bg-gray-500',
                profile.status === 'error' && 'bg-red-500'
              )}
            />
          </span>
          {isStarting ? `starting (${elapsedSeconds}s)` : profile.status}
        </span>
      </div>

      {/* Profile info */}
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-800">
          <Smartphone className="h-5 w-5 text-gray-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold truncate">{profile.name}</h3>
          <p className="text-sm text-gray-400 truncate">
            {profile.fingerprint.brand} {profile.fingerprint.model}
          </p>
        </div>
      </div>

      {/* Device details */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-gray-400">
        <div>
          <span className="text-gray-500">Android:</span>{' '}
          {profile.fingerprint.android_version}
        </div>
        <div>
          <span className="text-gray-500">Screen:</span>{' '}
          {profile.fingerprint.screen.width}x{profile.fingerprint.screen.height}
        </div>
        <div>
          <span className="text-gray-500">Proxy:</span>{' '}
          {profile.proxy.type === 'none' ? 'Direct' : profile.proxy.type}
        </div>
        <div>
          <span className="text-gray-500">Port:</span>{' '}
          {profile.adb_port || '-'}
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex items-center gap-2">
        {isRunning ? (
          <>
            <Link
              href={`/profiles/${profile.id}`}
              className="flex-1 flex items-center justify-center gap-2 rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
            >
              <Monitor className="h-4 w-4" />
              View
            </Link>
            <button
              onClick={() => stopMutation.mutate()}
              disabled={isLoading}
              className="flex items-center justify-center rounded-md bg-gray-700 px-3 py-2 text-sm font-medium hover:bg-gray-600 transition-colors disabled:opacity-50"
            >
              {isStopping ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Square className="h-4 w-4" />
              )}
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => startMutation.mutate()}
              disabled={isLoading || isStopping}
              className="flex-1 flex items-center justify-center gap-2 rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {isStarting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              Start
            </button>
            <button
              onClick={handleDelete}
              disabled={isLoading}
              className="flex items-center justify-center rounded-md bg-red-600/20 px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-600/30 transition-colors disabled:opacity-50"
            >
              {deleteMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

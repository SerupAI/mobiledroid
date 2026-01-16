'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Square, Settings, Loader2, Camera, Globe, Save, X, ExternalLink } from 'lucide-react';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { DeviceViewerWS } from '@/components/DeviceViewerWS';
import { DeviceControls } from '@/components/DeviceControls';
import { DeviceChat } from '@/components/DeviceChat';
import { QuickAppInstallPanel } from '@/components/QuickAppInstallPanel';
import { SnapshotList } from '@/components/SnapshotList';
import { CreateSnapshotModal } from '@/components/CreateSnapshotModal';
import { api, ProfileProxy, Proxy } from '@/lib/api';
import { cn, getStatusColor } from '@/lib/utils';

export default function ProfilePage() {
  const params = useParams();
  const profileId = params.id as string;
  const queryClient = useQueryClient();
  const [showCreateSnapshot, setShowCreateSnapshot] = useState(false);
  const [showProxyConfig, setShowProxyConfig] = useState(false);
  const [proxyConfig, setProxyConfig] = useState<ProfileProxy>({
    type: 'none',
    host: null,
    port: null,
    username: null,
    password: null,
  });
  const [proxyMode, setProxyMode] = useState<'pool' | 'manual'>('pool');
  const [selectedProxyId, setSelectedProxyId] = useState<number | null>(null);

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

  const { data: proxiesData } = useQuery({
    queryKey: ['proxies', 'active'],
    queryFn: () => api.getProxies(true),
    enabled: showProxyConfig,
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

  const proxyMutation = useMutation({
    mutationFn: (proxy: ProfileProxy) =>
      api.updateProfileProxy(profileId, proxy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile', profileId] });
      setShowProxyConfig(false);
    },
  });

  // Sync proxy config from profile
  useEffect(() => {
    if (profile?.proxy) {
      setProxyConfig({
        type: profile.proxy.type || 'none',
        host: profile.proxy.host || null,
        port: profile.proxy.port || null,
        username: profile.proxy.username || null,
        password: profile.proxy.password || null,
      });
    }
  }, [profile?.proxy]);

  const handleTap = (x: number, y: number) => {
    tapMutation.mutate({ x, y });
  };

  const handleSaveProxy = () => {
    proxyMutation.mutate(proxyConfig);
  };

  const handleSelectProxy = (proxyId: number | null) => {
    setSelectedProxyId(proxyId);
    if (proxyId === null) {
      setProxyConfig({
        type: 'none',
        host: null,
        port: null,
        username: null,
        password: null,
      });
    } else {
      const proxy = proxiesData?.proxies.find((p) => p.id === proxyId);
      if (proxy) {
        setProxyConfig({
          type: proxy.protocol as 'none' | 'http' | 'socks5',
          host: proxy.host,
          port: proxy.port,
          username: proxy.username,
          password: proxy.password,
        });
      }
    }
  };

  const poolProxies = proxiesData?.proxies || [];

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

              {/* Quick App Install */}
              <QuickAppInstallPanel profileId={profileId} profileStatus={profile.status} />

              {/* Task history */}
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold">Recent Tasks</h2>
                  <Link
                    href="/tasks"
                    className="text-xs text-primary-400 hover:text-primary-300"
                  >
                    View All
                  </Link>
                </div>
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
                          <div className="flex items-center gap-1.5">
                            <span
                              className={cn(
                                'text-xs px-2 py-0.5 rounded',
                                task.status === 'completed' && 'bg-green-500/20 text-green-400',
                                task.status === 'running' && 'bg-orange-500/20 text-orange-400',
                                task.status === 'queued' && 'bg-yellow-500/20 text-yellow-400',
                                task.status === 'failed' && 'bg-red-500/20 text-red-400',
                                task.status === 'cancelled' && 'bg-gray-500/20 text-gray-500',
                                (task.status === 'pending' || task.status === 'scheduled') && 'bg-gray-500/20 text-gray-400'
                              )}
                            >
                              {task.status}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between mt-2">
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <span>{task.steps_taken} steps</span>
                            {task.tokens_used > 0 && (
                              <span>{task.tokens_used.toLocaleString()} tokens</span>
                            )}
                          </div>
                          {task.chat_session_id && (
                            <Link
                              href={`/history?session=${task.chat_session_id}`}
                              className="inline-flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300"
                            >
                              <ExternalLink className="h-3 w-3" />
                              View Log
                            </Link>
                          )}
                        </div>
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

              {/* Proxy Configuration */}
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold">Proxy</h2>
                  <button
                    onClick={() => setShowProxyConfig(!showProxyConfig)}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-700 text-white rounded hover:bg-gray-600"
                  >
                    <Globe className="h-4 w-4" />
                    {showProxyConfig ? 'Cancel' : 'Configure'}
                  </button>
                </div>

                {/* Current proxy status */}
                {!showProxyConfig && (
                  <div className="text-sm">
                    {profile.proxy?.type === 'none' || !profile.proxy?.type ? (
                      <span className="text-gray-400">No proxy configured (direct connection)</span>
                    ) : (
                      <div className="space-y-1">
                        <div>
                          <span className="text-gray-500">Type:</span>{' '}
                          <span className="uppercase">{profile.proxy.type}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Server:</span>{' '}
                          {profile.proxy.host}:{profile.proxy.port}
                        </div>
                        {profile.proxy.username && (
                          <div>
                            <span className="text-gray-500">Auth:</span>{' '}
                            {profile.proxy.username}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Proxy configuration form */}
                {showProxyConfig && (
                  <div className="space-y-4">
                    {/* Mode selector */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => setProxyMode('pool')}
                        className={`flex-1 px-3 py-2 text-sm rounded-lg transition-colors ${
                          proxyMode === 'pool'
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                        }`}
                      >
                        Select from Pool
                      </button>
                      <button
                        onClick={() => setProxyMode('manual')}
                        className={`flex-1 px-3 py-2 text-sm rounded-lg transition-colors ${
                          proxyMode === 'manual'
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                        }`}
                      >
                        Manual Entry
                      </button>
                    </div>

                    {/* Pool selection */}
                    {proxyMode === 'pool' && (
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          Select Proxy
                        </label>
                        <select
                          value={selectedProxyId ?? ''}
                          onChange={(e) => handleSelectProxy(e.target.value ? parseInt(e.target.value) : null)}
                          className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                        >
                          <option value="">No Proxy (Direct)</option>
                          {poolProxies.map((proxy) => (
                            <option key={proxy.id} value={proxy.id}>
                              {proxy.protocol}://{proxy.host}:{proxy.port}
                              {proxy.name ? ` (${proxy.name})` : ''}
                              {proxy.country ? ` - ${proxy.country}` : ''}
                            </option>
                          ))}
                        </select>
                        {poolProxies.length === 0 && (
                          <p className="mt-2 text-xs text-gray-400">
                            No proxies in pool.{' '}
                            <a href="/proxies" className="text-primary-400 hover:text-primary-300">
                              Upload proxies
                            </a>{' '}
                            to get started.
                          </p>
                        )}
                        {selectedProxyId && proxyConfig.host && (
                          <div className="mt-2 text-xs text-gray-400">
                            <span className="font-mono">
                              {proxyConfig.type}://{proxyConfig.username ? `${proxyConfig.username}:***@` : ''}{proxyConfig.host}:{proxyConfig.port}
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Manual entry */}
                    {proxyMode === 'manual' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium mb-2">
                            Proxy Type
                          </label>
                          <select
                            value={proxyConfig.type}
                            onChange={(e) =>
                              setProxyConfig({ ...proxyConfig, type: e.target.value as 'none' | 'http' | 'socks5' })
                            }
                            className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                          >
                            <option value="none">No Proxy (Direct)</option>
                            <option value="http">HTTP Proxy</option>
                            <option value="socks5">SOCKS5 Proxy</option>
                          </select>
                          {proxyConfig.type === 'socks5' && (
                            <p className="mt-1 text-xs text-yellow-400">
                              Note: SOCKS5 support is limited in Android
                            </p>
                          )}
                        </div>

                        {proxyConfig.type !== 'none' && (
                          <>
                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <label className="block text-sm font-medium mb-2">
                                  Host
                                </label>
                                <input
                                  type="text"
                                  placeholder="proxy.example.com"
                                  value={proxyConfig.host || ''}
                                  onChange={(e) =>
                                    setProxyConfig({ ...proxyConfig, host: e.target.value || null })
                                  }
                                  className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium mb-2">
                                  Port
                                </label>
                                <input
                                  type="number"
                                  placeholder="8080"
                                  value={proxyConfig.port || ''}
                                  onChange={(e) =>
                                    setProxyConfig({ ...proxyConfig, port: e.target.value ? parseInt(e.target.value) : null })
                                  }
                                  className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                                />
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                              <div>
                                <label className="block text-sm font-medium mb-2">
                                  Username (optional)
                                </label>
                                <input
                                  type="text"
                                  placeholder="username"
                                  value={proxyConfig.username || ''}
                                  onChange={(e) =>
                                    setProxyConfig({ ...proxyConfig, username: e.target.value || null })
                                  }
                                  className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                                />
                              </div>
                              <div>
                                <label className="block text-sm font-medium mb-2">
                                  Password (optional)
                                </label>
                                <input
                                  type="password"
                                  placeholder="password"
                                  value={proxyConfig.password || ''}
                                  onChange={(e) =>
                                    setProxyConfig({ ...proxyConfig, password: e.target.value || null })
                                  }
                                  className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                                />
                              </div>
                            </div>
                          </>
                        )}
                      </>
                    )}

                    <div className="flex gap-2 pt-2">
                      <button
                        onClick={handleSaveProxy}
                        disabled={proxyMutation.isPending}
                        className="flex items-center gap-2 px-4 py-2 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                      >
                        {proxyMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4" />
                        )}
                        Save Proxy
                      </button>
                      <button
                        onClick={() => setShowProxyConfig(false)}
                        className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-700 text-white rounded hover:bg-gray-600"
                      >
                        <X className="h-4 w-4" />
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
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

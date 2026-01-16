'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Package,
  Download,
  Check,
  AlertCircle,
  Loader2,
  Play,
  ChevronDown,
  ChevronUp,
  Store,
  Layers,
  RefreshCw,
} from 'lucide-react';
import { api, AppInfo, AppBundle, InstalledApp } from '@/lib/api';

interface QuickAppInstallPanelProps {
  profileId: string;
  profileStatus: string;
}

type CategoryFilter = 'all' | 'social' | 'messaging' | 'productivity' | 'entertainment' | 'utilities';

export function QuickAppInstallPanel({ profileId, profileStatus }: QuickAppInstallPanelProps) {
  const queryClient = useQueryClient();
  const [isExpanded, setIsExpanded] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>('all');
  const [activeTab, setActiveTab] = useState<'apps' | 'bundles'>('apps');
  const [installingApp, setInstallingApp] = useState<string | null>(null);
  const [installingBundle, setInstallingBundle] = useState<string | null>(null);

  const isRunning = profileStatus === 'running';

  // Fetch available apps
  const { data: appsData, isLoading: loadingApps } = useQuery({
    queryKey: ['available-apps', selectedCategory === 'all' ? undefined : selectedCategory],
    queryFn: () => api.getAvailableApps(selectedCategory === 'all' ? undefined : selectedCategory),
    enabled: isRunning,
  });

  // Fetch app bundles
  const { data: bundlesData, isLoading: loadingBundles } = useQuery({
    queryKey: ['app-bundles'],
    queryFn: () => api.getAppBundles(),
    enabled: isRunning,
  });

  // Fetch installed apps
  const { data: installedData, isLoading: loadingInstalled, refetch: refetchInstalled } = useQuery({
    queryKey: ['installed-apps', profileId],
    queryFn: () => api.getInstalledApps(profileId),
    enabled: isRunning,
    refetchOnWindowFocus: false,
  });

  // Check Aurora Store status
  const { data: auroraStatus, isLoading: loadingAurora } = useQuery({
    queryKey: ['aurora-status', profileId],
    queryFn: () => api.checkAuroraStatus(profileId),
    enabled: isRunning,
    refetchOnWindowFocus: false,
  });

  // Install app mutation
  const installAppMutation = useMutation({
    mutationFn: async (appId: string) => {
      setInstallingApp(appId);
      return api.installApp(profileId, appId, { wait_for_install: true, timeout: 120 });
    },
    onSuccess: (result) => {
      setInstallingApp(null);
      if (result.success) {
        refetchInstalled();
      }
    },
    onError: () => {
      setInstallingApp(null);
    },
  });

  // Install bundle mutation
  const installBundleMutation = useMutation({
    mutationFn: async (bundleId: string) => {
      setInstallingBundle(bundleId);
      return api.installBundle(profileId, bundleId, { sequential: true });
    },
    onSuccess: (result) => {
      setInstallingBundle(null);
      if (result.success) {
        refetchInstalled();
      }
    },
    onError: () => {
      setInstallingBundle(null);
    },
  });

  // Launch app mutation
  const launchAppMutation = useMutation({
    mutationFn: (appId: string) => api.launchApp(profileId, appId),
  });

  const installedPackages = new Set(installedData?.apps.map(a => a.package) || []);

  const isAppInstalled = (app: AppInfo) => installedPackages.has(app.package);

  const categories: { value: CategoryFilter; label: string }[] = [
    { value: 'all', label: 'All' },
    { value: 'social', label: 'Social' },
    { value: 'messaging', label: 'Messaging' },
    { value: 'productivity', label: 'Productivity' },
    { value: 'entertainment', label: 'Entertainment' },
    { value: 'utilities', label: 'Utilities' },
  ];

  if (!isRunning) {
    return (
      <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5 text-gray-400" />
            <h3 className="text-lg font-semibold">Quick App Install</h3>
          </div>
        </div>
        <div className="p-6 text-center text-gray-500">
          <Store className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Start the profile to install apps</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
      {/* Header */}
      <div
        className="p-4 border-b border-gray-800 flex justify-between items-center cursor-pointer hover:bg-gray-800/50"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Package className="h-5 w-5 text-primary-400" />
          <h3 className="text-lg font-semibold">Quick App Install</h3>
          {auroraStatus && !auroraStatus.installed && (
            <span className="text-xs px-2 py-0.5 bg-yellow-900/50 text-yellow-400 rounded">
              Aurora Store required
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              refetchInstalled();
            }}
            className="p-1 text-gray-400 hover:text-white"
            title="Refresh installed apps"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Tabs */}
          <div className="flex border-b border-gray-800">
            <button
              onClick={() => setActiveTab('apps')}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'apps'
                  ? 'text-primary-400 border-b-2 border-primary-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Store className="h-4 w-4 inline-block mr-1.5" />
              Apps
            </button>
            <button
              onClick={() => setActiveTab('bundles')}
              className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'bundles'
                  ? 'text-primary-400 border-b-2 border-primary-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Layers className="h-4 w-4 inline-block mr-1.5" />
              Bundles
            </button>
          </div>

          {activeTab === 'apps' && (
            <>
              {/* Category Filter */}
              <div className="p-3 border-b border-gray-800 bg-gray-950">
                <div className="flex gap-1 flex-wrap">
                  {categories.map((cat) => (
                    <button
                      key={cat.value}
                      onClick={() => setSelectedCategory(cat.value)}
                      className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                        selectedCategory === cat.value
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Apps List */}
              <div className="max-h-64 overflow-y-auto">
                {loadingApps || loadingInstalled ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                    <span className="ml-2 text-gray-400 text-sm">Loading apps...</span>
                  </div>
                ) : appsData?.apps.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 text-sm">
                    No apps available in this category
                  </div>
                ) : (
                  <div className="divide-y divide-gray-800">
                    {appsData?.apps.map((app) => {
                      const installed = isAppInstalled(app);
                      const isInstalling = installingApp === app.id;

                      return (
                        <div
                          key={app.id}
                          className="flex items-center justify-between p-3 hover:bg-gray-800/50"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-200 truncate">
                              {app.name}
                            </p>
                            <p className="text-xs text-gray-500 truncate">
                              {app.package}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 ml-3">
                            {installed ? (
                              <>
                                <span className="text-xs text-green-400 flex items-center gap-1">
                                  <Check className="h-3 w-3" />
                                  Installed
                                </span>
                                <button
                                  onClick={() => launchAppMutation.mutate(app.id)}
                                  disabled={launchAppMutation.isPending}
                                  className="p-1.5 bg-primary-600 hover:bg-primary-700 rounded text-white disabled:opacity-50"
                                  title="Launch app"
                                >
                                  <Play className="h-3.5 w-3.5" />
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => installAppMutation.mutate(app.id)}
                                disabled={isInstalling || installingApp !== null}
                                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-green-600 hover:bg-green-700 rounded text-white text-xs disabled:opacity-50"
                              >
                                {isInstalling ? (
                                  <>
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    Installing...
                                  </>
                                ) : (
                                  <>
                                    <Download className="h-3.5 w-3.5" />
                                    Install
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          )}

          {activeTab === 'bundles' && (
            <div className="max-h-64 overflow-y-auto">
              {loadingBundles ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
                  <span className="ml-2 text-gray-400 text-sm">Loading bundles...</span>
                </div>
              ) : bundlesData?.bundles.length === 0 ? (
                <div className="text-center py-8 text-gray-500 text-sm">
                  No app bundles available
                </div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {bundlesData?.bundles.map((bundle) => {
                    const isInstalling = installingBundle === bundle.id;

                    return (
                      <div
                        key={bundle.id}
                        className="p-3 hover:bg-gray-800/50"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-200">
                              {bundle.name}
                            </p>
                            <p className="text-xs text-gray-500 mt-0.5">
                              {bundle.description}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              {bundle.app_count} apps: {bundle.apps.join(', ')}
                            </p>
                          </div>
                          <button
                            onClick={() => installBundleMutation.mutate(bundle.id)}
                            disabled={isInstalling || installingBundle !== null}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-primary-600 hover:bg-primary-700 rounded text-white text-xs disabled:opacity-50 ml-3 flex-shrink-0"
                          >
                            {isInstalling ? (
                              <>
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                Installing...
                              </>
                            ) : (
                              <>
                                <Layers className="h-3.5 w-3.5" />
                                Install All
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Install Status */}
          {(installAppMutation.isSuccess || installBundleMutation.isSuccess) && (
            <div className="p-3 bg-green-900/20 border-t border-green-800">
              <p className="text-sm text-green-400 flex items-center gap-2">
                <Check className="h-4 w-4" />
                {installAppMutation.isSuccess
                  ? installAppMutation.data?.installed
                    ? 'App installed successfully!'
                    : installAppMutation.data?.already_installed
                    ? 'App was already installed'
                    : 'Installation initiated'
                  : `Bundle installed: ${installBundleMutation.data?.success_count} success, ${installBundleMutation.data?.skip_count} skipped`}
              </p>
            </div>
          )}

          {/* Error Status */}
          {(installAppMutation.isError || installBundleMutation.isError) && (
            <div className="p-3 bg-red-900/20 border-t border-red-800">
              <p className="text-sm text-red-400 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Installation failed. Please try again.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

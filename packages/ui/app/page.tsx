'use client';

import { useQuery } from '@tanstack/react-query';
import { Smartphone, Activity, Cpu, HardDrive } from 'lucide-react';
import { Header } from '@/components/Header';
import { ProfileCard } from '@/components/ProfileCard';
import { CreateProfileCard } from '@/components/CreateProfileCard';
import { api } from '@/lib/api';

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.getProfiles(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const profiles = data?.profiles || [];
  const runningCount = profiles.filter((p) => p.status === 'running').length;

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/10">
                <Smartphone className="h-5 w-5 text-primary-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{profiles.length}</p>
                <p className="text-sm text-gray-400">Total Profiles</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <Activity className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{runningCount}</p>
                <p className="text-sm text-gray-400">Running</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-500/10">
                <Cpu className="h-5 w-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">-</p>
                <p className="text-sm text-gray-400">CPU Usage</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <HardDrive className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">-</p>
                <p className="text-sm text-gray-400">Memory</p>
              </div>
            </div>
          </div>
        </div>

        {/* Section header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Device Profiles</h2>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
            Failed to load profiles: {(error as Error).message}
          </div>
        )}

        {/* Profiles grid */}
        {!isLoading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {profiles.map((profile) => (
              <ProfileCard key={profile.id} profile={profile} />
            ))}
            <CreateProfileCard />
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && profiles.length === 0 && (
          <div className="text-center py-12">
            <Smartphone className="mx-auto h-12 w-12 text-gray-600 mb-4" />
            <h3 className="text-lg font-medium mb-2">No profiles yet</h3>
            <p className="text-gray-400 mb-4">
              Create your first device profile to get started
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

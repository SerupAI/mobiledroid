'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Header } from '@/components/Header';
import { SnapshotList } from '@/components/SnapshotList';
import {
  Camera,
  Filter,
  Loader2,
  HardDrive,
} from 'lucide-react';
import { api, Profile } from '@/lib/api';

export default function SnapshotsPage() {
  const [filterDevice, setFilterDevice] = useState<string>('all');

  // Fetch profiles for filtering
  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.getProfiles(),
  });

  // Fetch all snapshots to get stats
  const { data: allSnapshots, isLoading } = useQuery({
    queryKey: ['snapshots'],
    queryFn: () => api.listSnapshots(),
  });

  const profiles: Profile[] = profilesData?.profiles || [];
  const snapshots = allSnapshots || [];

  // Calculate stats
  const totalSize = snapshots.reduce((sum, s) => sum + (s.size_bytes || 0), 0);
  const completedCount = snapshots.filter(s => s.status === 'ready').length;

  const formatBytes = (bytes: number): string => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Camera className="h-6 w-6 text-primary-500" />
              Snapshots
            </h1>
            <p className="text-gray-400 mt-1">
              Manage device snapshots across all profiles
            </p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/10">
                <Camera className="h-5 w-5 text-primary-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{snapshots.length}</p>
                <p className="text-sm text-gray-400">Total Snapshots</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <Camera className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{completedCount}</p>
                <p className="text-sm text-gray-400">Ready to Restore</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <HardDrive className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatBytes(totalSize)}</p>
                <p className="text-sm text-gray-400">Total Storage</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={filterDevice}
              onChange={(e) => setFilterDevice(e.target.value)}
              className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Devices</option>
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          </div>
        )}

        {/* Snapshots List */}
        {!isLoading && (
          <SnapshotList
            profileId={filterDevice === 'all' ? undefined : filterDevice}
          />
        )}
      </main>
    </div>
  );
}

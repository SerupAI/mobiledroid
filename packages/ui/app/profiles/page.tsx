'use client';

import { useQuery } from '@tanstack/react-query';
import { Smartphone, Plus, Search, Filter } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { Header } from '@/components/Header';
import { ProfileCard } from '@/components/ProfileCard';
import { api } from '@/lib/api';

export default function ProfilesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const { data, isLoading, error } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => api.getProfiles(),
    refetchInterval: 5000,
  });

  const profiles = data?.profiles || [];

  // Filter profiles
  const filteredProfiles = profiles.filter((profile) => {
    const matchesSearch =
      profile.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      profile.fingerprint.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      profile.fingerprint.brand.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || profile.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">Device Profiles</h1>
            <p className="text-gray-400 mt-1">
              Manage your Android device profiles
            </p>
          </div>
          <Link
            href="/profiles/new"
            className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Profile
          </Link>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search profiles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 pl-10 pr-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="all">All Status</option>
              <option value="running">Running</option>
              <option value="stopped">Stopped</option>
              <option value="starting">Starting</option>
              <option value="error">Error</option>
            </select>
          </div>
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
            {filteredProfiles.map((profile) => (
              <ProfileCard key={profile.id} profile={profile} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && filteredProfiles.length === 0 && (
          <div className="text-center py-12">
            <Smartphone className="mx-auto h-12 w-12 text-gray-600 mb-4" />
            <h3 className="text-lg font-medium mb-2">
              {profiles.length === 0 ? 'No profiles yet' : 'No matching profiles'}
            </h3>
            <p className="text-gray-400 mb-4">
              {profiles.length === 0
                ? 'Create your first device profile to get started'
                : 'Try adjusting your search or filter criteria'}
            </p>
            {profiles.length === 0 && (
              <Link
                href="/profiles/new"
                className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 transition-colors"
              >
                <Plus className="h-4 w-4" />
                Create Profile
              </Link>
            )}
          </div>
        )}

        {/* Profile count */}
        {!isLoading && !error && filteredProfiles.length > 0 && (
          <div className="mt-6 text-center text-sm text-gray-400">
            Showing {filteredProfiles.length} of {profiles.length} profiles
          </div>
        )}
      </main>
    </div>
  );
}

'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Header } from '@/components/Header';
import {
  History,
  Loader2,
  MessageSquare,
  DollarSign,
  Smartphone,
  ChevronRight,
  Filter,
  Search
} from 'lucide-react';

interface ChatSessionSummary {
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

interface ChatHistoryResponse {
  sessions: ChatSessionSummary[];
  total_tokens: number;
  total_sessions: number;
}

interface Profile {
  id: string;
  name: string;
  status: string;
}

// Claude Sonnet pricing (per 1K tokens)
const COST_PER_1K_INPUT = 0.003;
const COST_PER_1K_OUTPUT = 0.015;

function calculateCost(tokens: number): number {
  const inputTokens = tokens / 2;
  const outputTokens = tokens / 2;
  return (inputTokens / 1000 * COST_PER_1K_INPUT) + (outputTokens / 1000 * COST_PER_1K_OUTPUT);
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return 'Today ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (days === 1) {
    return 'Yesterday ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (days < 7) {
    return `${days} days ago`;
  } else {
    return date.toLocaleDateString();
  }
}

export default function HistoryPage() {
  const [filterDevice, setFilterDevice] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch all chat history
  const { data: historyData, isLoading: historyLoading } = useQuery<ChatHistoryResponse>({
    queryKey: ['chat-history'],
    queryFn: async () => {
      const response = await fetch(`/api/chat/history?limit=500`);
      if (!response.ok) throw new Error('Failed to fetch history');
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch profiles for filtering
  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: async () => {
      const response = await fetch(`/api/profiles`);
      if (!response.ok) throw new Error('Failed to fetch profiles');
      return response.json();
    },
  });

  const profiles: Profile[] = profilesData?.profiles || [];
  const sessions = historyData?.sessions || [];

  // Filter sessions
  const filteredSessions = sessions.filter(session => {
    const matchesDevice = filterDevice === 'all' || session.profile_id === filterDevice;
    const matchesSearch = searchQuery === '' ||
      session.initial_prompt.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDevice && matchesSearch;
  });

  // Group sessions by date
  const groupedSessions = filteredSessions.reduce((groups, session) => {
    const date = new Date(session.created_at).toLocaleDateString();
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(session);
    return groups;
  }, {} as Record<string, ChatSessionSummary[]>);

  // Get profile name by ID
  const getProfileName = (profileId: string) => {
    const profile = profiles.find(p => p.id === profileId);
    return profile?.name || 'Unknown Device';
  };

  // Calculate totals for filtered results
  const filteredTotalTokens = filteredSessions.reduce((sum, s) => sum + s.total_tokens, 0);
  const filteredTotalCost = calculateCost(filteredTotalTokens);

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <History className="h-6 w-6 text-primary-500" />
              Chat History
            </h1>
            <p className="text-gray-400 mt-1">
              View all chat sessions across your devices
            </p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-500/10">
                <MessageSquare className="h-5 w-5 text-primary-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{historyData?.total_sessions || 0}</p>
                <p className="text-sm text-gray-400">Total Sessions</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <MessageSquare className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{filteredSessions.length}</p>
                <p className="text-sm text-gray-400">Filtered Sessions</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-yellow-500/10">
                <span className="text-yellow-500 font-mono text-sm">TKN</span>
              </div>
              <div>
                <p className="text-2xl font-bold">{filteredTotalTokens.toLocaleString()}</p>
                <p className="text-sm text-gray-400">Total Tokens</p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <DollarSign className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold text-green-400">${filteredTotalCost.toFixed(4)}</p>
                <p className="text-sm text-gray-400">Estimated Cost</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
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

          <div className="flex items-center gap-2 flex-1 max-w-md">
            <Search className="h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search prompts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Loading State */}
        {historyLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          </div>
        )}

        {/* Empty State */}
        {!historyLoading && filteredSessions.length === 0 && (
          <div className="text-center py-12">
            <History className="mx-auto h-12 w-12 text-gray-600 mb-4" />
            <h3 className="text-lg font-medium mb-2">No chat history yet</h3>
            <p className="text-gray-400">
              Start chatting with your devices to see history here
            </p>
          </div>
        )}

        {/* Sessions List */}
        {!historyLoading && filteredSessions.length > 0 && (
          <div className="space-y-6">
            {Object.entries(groupedSessions).map(([date, dateSessions]) => (
              <div key={date}>
                <h3 className="text-sm font-medium text-gray-400 mb-3">{date}</h3>
                <div className="space-y-2">
                  {dateSessions.map((session) => (
                    <Link
                      key={session.id}
                      href={`/profiles/${session.profile_id}?chat=${session.id}`}
                      className="block"
                    >
                      <div className="flex items-center justify-between p-4 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 hover:bg-gray-800/50 transition-colors cursor-pointer">
                        <div className="flex items-center gap-4 flex-1 min-w-0">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-800">
                            <Smartphone className="h-5 w-5 text-gray-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">
                              {session.initial_prompt}
                            </p>
                            <div className="flex items-center gap-3 mt-1 text-sm text-gray-400">
                              <span>{getProfileName(session.profile_id)}</span>
                              <span>·</span>
                              <span>{formatDate(session.created_at)}</span>
                              <span>·</span>
                              <span>{session.total_steps} steps</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 ml-4">
                          <span className={`text-xs px-2 py-1 rounded ${
                            session.status === 'completed' ? 'bg-green-900/50 text-green-400' :
                            session.status === 'error' ? 'bg-red-900/50 text-red-400' :
                            session.status === 'cancelled' ? 'bg-orange-900/50 text-orange-400' :
                            'bg-gray-700 text-gray-400'
                          }`}>
                            {session.status}
                          </span>
                          <div className="text-right min-w-[100px]">
                            <p className="text-sm font-medium">
                              {session.total_tokens.toLocaleString()} tokens
                            </p>
                            <p className="text-xs text-green-400">
                              ${calculateCost(session.total_tokens).toFixed(4)}
                            </p>
                          </div>
                          <ChevronRight className="h-5 w-5 text-gray-600" />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

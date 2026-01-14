'use client';

import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Globe,
  Upload,
  Trash2,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  FileText,
  Plus,
  X,
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, Proxy } from '@/lib/api';

export default function ProxiesPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadResult, setUploadResult] = useState<{
    imported: number;
    skipped: number;
    errors: string[];
  } | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newProxy, setNewProxy] = useState({
    protocol: 'http' as 'http' | 'socks5',
    host: '',
    port: '',
    username: '',
    password: '',
    name: '',
    country: '',
  });

  const { data: proxiesData, isLoading } = useQuery({
    queryKey: ['proxies'],
    queryFn: () => api.getProxies(),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadProxies(file),
    onSuccess: (result) => {
      setUploadResult(result);
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: { protocol: string; host: string; port: number; username?: string; password?: string; name?: string; country?: string }) =>
      api.createProxy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
      setShowAddForm(false);
      setNewProxy({
        protocol: 'http',
        host: '',
        port: '',
        username: '',
        password: '',
        name: '',
        country: '',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (proxyId: number) => api.deleteProxy(proxyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
    },
  });

  const deleteAllMutation = useMutation({
    mutationFn: () => api.deleteAllProxies(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api.updateProxy(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxies'] });
    },
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadResult(null);
      uploadMutation.mutate(file);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDeleteAll = () => {
    if (confirm('Are you sure you want to delete ALL proxies? This cannot be undone.')) {
      deleteAllMutation.mutate();
    }
  };

  const handleAddProxy = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProxy.host || !newProxy.port) return;
    createMutation.mutate({
      protocol: newProxy.protocol,
      host: newProxy.host,
      port: parseInt(newProxy.port),
      username: newProxy.username || undefined,
      password: newProxy.password || undefined,
      name: newProxy.name || undefined,
      country: newProxy.country || undefined,
    });
  };

  const formatProxyUrl = (proxy: Proxy): string => {
    let url = `${proxy.protocol}://`;
    if (proxy.username && proxy.password) {
      url += `${proxy.username}:***@`;
    }
    url += `${proxy.host}:${proxy.port}`;
    return url;
  };

  const proxies = proxiesData?.proxies || [];

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              <Globe className="h-7 w-7 text-primary-400" />
              Proxy Pool
            </h1>
            <p className="text-gray-400 mt-1">
              Manage your proxy pool for device profiles
            </p>
          </div>

          <div className="flex items-center gap-3">
            {proxies.length > 0 && (
              <button
                onClick={handleDeleteAll}
                disabled={deleteAllMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 rounded-lg border border-red-500/50 text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
              >
                {deleteAllMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                Delete All
              </button>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.csv"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-600 text-white hover:bg-gray-800 transition-colors disabled:opacity-50"
            >
              {uploadMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Upload className="h-4 w-4" />
              )}
              Upload File
            </button>
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showAddForm
                  ? 'bg-gray-700 text-white'
                  : 'bg-primary-600 text-white hover:bg-primary-700'
              }`}
            >
              {showAddForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              {showAddForm ? 'Cancel' : 'Add Proxy'}
            </button>
          </div>
        </div>

        {/* Add single proxy form */}
        {showAddForm && (
          <div className="mb-6 rounded-lg border border-gray-800 bg-gray-900 p-4">
            <h3 className="font-medium mb-4">Add Single Proxy</h3>
            <form onSubmit={handleAddProxy} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-400">Protocol</label>
                  <select
                    value={newProxy.protocol}
                    onChange={(e) => setNewProxy({ ...newProxy, protocol: e.target.value as 'http' | 'socks5' })}
                    className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                  >
                    <option value="http">HTTP</option>
                    <option value="socks5">SOCKS5</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium mb-1 text-gray-400">Host *</label>
                  <input
                    type="text"
                    value={newProxy.host}
                    onChange={(e) => setNewProxy({ ...newProxy, host: e.target.value })}
                    placeholder="proxy.example.com"
                    className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-400">Port *</label>
                  <input
                    type="number"
                    value={newProxy.port}
                    onChange={(e) => setNewProxy({ ...newProxy, port: e.target.value })}
                    placeholder="8080"
                    min="1"
                    max="65535"
                    className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-400">Username</label>
                  <input
                    type="text"
                    value={newProxy.username}
                    onChange={(e) => setNewProxy({ ...newProxy, username: e.target.value })}
                    placeholder="optional"
                    className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-400">Password</label>
                  <input
                    type="password"
                    value={newProxy.password}
                    onChange={(e) => setNewProxy({ ...newProxy, password: e.target.value })}
                    placeholder="optional"
                    className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-400">Name</label>
                  <input
                    type="text"
                    value={newProxy.name}
                    onChange={(e) => setNewProxy({ ...newProxy, name: e.target.value })}
                    placeholder="friendly name"
                    className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 text-gray-400">Country</label>
                  <input
                    type="text"
                    value={newProxy.country}
                    onChange={(e) => setNewProxy({ ...newProxy, country: e.target.value.toUpperCase().slice(0, 2) })}
                    placeholder="US"
                    maxLength={2}
                    className="w-full rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 rounded-lg border border-gray-600 text-gray-400 hover:bg-gray-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newProxy.host || !newProxy.port || createMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                  Add Proxy
                </button>
              </div>

              {createMutation.isError && (
                <div className="text-sm text-red-400 mt-2">
                  {(createMutation.error as Error).message}
                </div>
              )}
            </form>
          </div>
        )}

        {/* Upload result notification */}
        {uploadResult && (
          <div className={`mb-6 rounded-lg border p-4 ${
            uploadResult.errors.length > 0
              ? 'border-yellow-500/30 bg-yellow-500/10'
              : 'border-green-500/30 bg-green-500/10'
          }`}>
            <div className="flex items-start gap-3">
              {uploadResult.errors.length > 0 ? (
                <AlertCircle className="h-5 w-5 text-yellow-400 mt-0.5" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
              )}
              <div className="flex-1">
                <h4 className={`font-medium ${
                  uploadResult.errors.length > 0 ? 'text-yellow-400' : 'text-green-400'
                }`}>
                  Upload Complete
                </h4>
                <p className="text-sm mt-1 text-gray-300">
                  Imported: {uploadResult.imported} | Skipped (duplicates): {uploadResult.skipped}
                  {uploadResult.errors.length > 0 && ` | Errors: ${uploadResult.errors.length}`}
                </p>
                {uploadResult.errors.length > 0 && (
                  <ul className="mt-2 text-sm text-yellow-300/80 list-disc list-inside">
                    {uploadResult.errors.slice(0, 5).map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                    {uploadResult.errors.length > 5 && (
                      <li>...and {uploadResult.errors.length - 5} more errors</li>
                    )}
                  </ul>
                )}
              </div>
              <button
                onClick={() => setUploadResult(null)}
                className="text-gray-400 hover:text-gray-300"
              >
                <XCircle className="h-5 w-5" />
              </button>
            </div>
          </div>
        )}

        {/* Supported formats info */}
        <div className="mb-6 rounded-lg border border-gray-800 bg-gray-900 p-4">
          <div className="flex items-start gap-3">
            <FileText className="h-5 w-5 text-gray-400 mt-0.5" />
            <div>
              <h4 className="font-medium text-gray-300">Supported Formats</h4>
              <p className="text-sm text-gray-400 mt-1">
                Upload a text file with one proxy per line. Supported formats:
              </p>
              <ul className="mt-2 text-sm text-gray-500 font-mono space-y-1">
                <li>host:port</li>
                <li>host:port:username:password</li>
                <li>username:password@host:port</li>
                <li>http://host:port</li>
                <li>socks5://username:password@host:port</li>
              </ul>
              <p className="text-sm text-gray-500 mt-2">Lines starting with # are ignored.</p>
            </div>
          </div>
        </div>

        {/* Proxies list */}
        <div className="rounded-lg border border-gray-800 bg-gray-900">
          <div className="p-4 border-b border-gray-800">
            <h2 className="font-semibold">
              Proxies ({proxiesData?.total || 0})
            </h2>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : proxies.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <Globe className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-lg">No proxies in pool</p>
              <p className="text-sm mt-1">Upload a proxy file to get started</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-800">
              {proxies.map((proxy) => (
                <div
                  key={proxy.id}
                  className="flex items-center justify-between p-4 hover:bg-gray-800/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() =>
                        toggleActiveMutation.mutate({
                          id: proxy.id,
                          is_active: !proxy.is_active,
                        })
                      }
                      className={`h-8 w-8 rounded-full flex items-center justify-center transition-colors ${
                        proxy.is_active
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-700 text-gray-500'
                      }`}
                      title={proxy.is_active ? 'Active - click to disable' : 'Inactive - click to enable'}
                    >
                      {proxy.is_active ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        <XCircle className="h-4 w-4" />
                      )}
                    </button>

                    <div>
                      <div className="flex items-center gap-2">
                        <code className="text-sm font-mono">
                          {formatProxyUrl(proxy)}
                        </code>
                        <span className={`px-1.5 py-0.5 rounded text-xs uppercase ${
                          proxy.protocol === 'http'
                            ? 'bg-blue-500/20 text-blue-400'
                            : proxy.protocol === 'socks5'
                            ? 'bg-purple-500/20 text-purple-400'
                            : 'bg-gray-500/20 text-gray-400'
                        }`}>
                          {proxy.protocol}
                        </span>
                        {proxy.name && (
                          <span className="text-gray-500">({proxy.name})</span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                        {proxy.country && <span>Country: {proxy.country}</span>}
                        {proxy.times_used > 0 && (
                          <span className="text-gray-400">
                            Used: {proxy.times_used}x
                          </span>
                        )}
                        {proxy.is_working === false && (
                          <span className="text-yellow-500">
                            Not working
                          </span>
                        )}
                        <span>
                          Added: {new Date(proxy.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => deleteMutation.mutate(proxy.id)}
                    disabled={deleteMutation.isPending}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Delete proxy"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

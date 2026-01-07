'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { Header } from '@/components/Header';
import { api, DeviceFingerprint, ProfileCreate } from '@/lib/api';

export default function NewProfilePage() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [proxyType, setProxyType] = useState<'none' | 'http' | 'socks5'>('none');
  const [proxyHost, setProxyHost] = useState('');
  const [proxyPort, setProxyPort] = useState('');
  const [proxyUsername, setProxyUsername] = useState('');
  const [proxyPassword, setProxyPassword] = useState('');

  const { data: fingerprintData, isLoading: loadingFingerprints } = useQuery({
    queryKey: ['fingerprints'],
    queryFn: () => api.getFingerprints(),
  });

  const fingerprints = fingerprintData?.fingerprints || [];

  const createMutation = useMutation({
    mutationFn: async (data: ProfileCreate) => {
      return api.createProfile(data);
    },
    onSuccess: (profile) => {
      router.push('/');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const selectedFingerprint = fingerprints.find(
      (fp) => fp.id === selectedDevice
    );
    if (!selectedFingerprint || !name.trim()) return;

    const profileData: ProfileCreate = {
      name: name.trim(),
      fingerprint: {
        model: selectedFingerprint.model,
        brand: selectedFingerprint.brand,
        manufacturer: selectedFingerprint.manufacturer,
        build_fingerprint: selectedFingerprint.build_fingerprint,
        android_version: selectedFingerprint.android_version,
        sdk_version: selectedFingerprint.sdk_version,
        hardware: '',
        board: '',
        product: '',
        screen: selectedFingerprint.screen,
        timezone: 'America/New_York',
        locale: 'en_US',
      },
      proxy: {
        type: proxyType,
        host: proxyType !== 'none' ? proxyHost : null,
        port: proxyType !== 'none' ? parseInt(proxyPort) || null : null,
        username: proxyUsername || null,
        password: proxyPassword || null,
      },
    };

    createMutation.mutate(profileData);
  };

  const selectedFingerprint = fingerprints.find(
    (fp) => fp.id === selectedDevice
  );

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8 max-w-2xl">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>

        <h1 className="text-2xl font-bold mb-8">Create New Profile</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Profile Name */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Profile Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., My Samsung S24"
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
              required
            />
          </div>

          {/* Device Selection */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Device Fingerprint
            </label>
            {loadingFingerprints ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                {fingerprints.map((fp) => (
                  <button
                    key={fp.id}
                    type="button"
                    onClick={() => setSelectedDevice(fp.id)}
                    className={`flex items-center justify-between rounded-lg border p-3 text-left transition-colors ${
                      selectedDevice === fp.id
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                    }`}
                  >
                    <div>
                      <p className="font-medium">{fp.name}</p>
                      <p className="text-sm text-gray-400">
                        Android {fp.android_version} &bull;{' '}
                        {fp.screen.width}x{fp.screen.height}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500 uppercase">
                      {fp.brand}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Proxy Configuration */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Proxy Configuration
            </label>
            <select
              value={proxyType}
              onChange={(e) =>
                setProxyType(e.target.value as 'none' | 'http' | 'socks5')
              }
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white focus:border-primary-500 focus:outline-none mb-3"
            >
              <option value="none">No Proxy (Direct Connection)</option>
              <option value="http">HTTP/HTTPS Proxy</option>
              <option value="socks5">SOCKS5 Proxy</option>
            </select>

            {proxyType !== 'none' && (
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  value={proxyHost}
                  onChange={(e) => setProxyHost(e.target.value)}
                  placeholder="Host"
                  className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
                />
                <input
                  type="number"
                  value={proxyPort}
                  onChange={(e) => setProxyPort(e.target.value)}
                  placeholder="Port"
                  className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
                />
                <input
                  type="text"
                  value={proxyUsername}
                  onChange={(e) => setProxyUsername(e.target.value)}
                  placeholder="Username (optional)"
                  className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
                />
                <input
                  type="password"
                  value={proxyPassword}
                  onChange={(e) => setProxyPassword(e.target.value)}
                  placeholder="Password (optional)"
                  className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white placeholder-gray-500 focus:border-primary-500 focus:outline-none"
                />
              </div>
            )}
          </div>

          {/* Selected device preview */}
          {selectedFingerprint && (
            <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
              <h3 className="font-medium mb-2">Selected Device</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Brand:</span>{' '}
                  {selectedFingerprint.brand}
                </div>
                <div>
                  <span className="text-gray-500">Model:</span>{' '}
                  {selectedFingerprint.model}
                </div>
                <div>
                  <span className="text-gray-500">Android:</span>{' '}
                  {selectedFingerprint.android_version}
                </div>
                <div>
                  <span className="text-gray-500">SDK:</span>{' '}
                  {selectedFingerprint.sdk_version}
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">Screen:</span>{' '}
                  {selectedFingerprint.screen.width}x
                  {selectedFingerprint.screen.height} @{' '}
                  {selectedFingerprint.screen.dpi}dpi
                </div>
              </div>
            </div>
          )}

          {/* Error message */}
          {createMutation.error && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
              {(createMutation.error as Error).message}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={
              !name.trim() || !selectedDevice || createMutation.isPending
            }
            className="w-full rounded-lg bg-primary-600 px-4 py-3 font-medium text-white hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createMutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                Creating...
              </span>
            ) : (
              'Create Profile'
            )}
          </button>
        </form>
      </main>
    </div>
  );
}

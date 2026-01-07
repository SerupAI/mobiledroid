'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Settings,
  Server,
  Key,
  Database,
  Globe,
  Shield,
  Bell,
  Palette,
  Save,
  RefreshCw,
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api } from '@/lib/api';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
  });

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'api', label: 'API Keys', icon: Key },
    { id: 'docker', label: 'Docker', icon: Server },
    { id: 'proxy', label: 'Proxy', icon: Globe },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
  ];

  return (
    <div className="min-h-screen bg-gray-950">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-gray-400 mt-1">
            Configure MobileDroid to your preferences
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <div className="w-full lg:w-64 flex-shrink-0">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-left transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                </button>
              ))}
            </nav>

            {/* System info */}
            <div className="mt-8 rounded-lg border border-gray-800 bg-gray-900 p-4">
              <h3 className="text-sm font-medium text-gray-400 mb-3">
                System Info
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Version</span>
                  <span>{health?.version || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Status</span>
                  <span className={health?.status === 'healthy' ? 'text-green-400' : 'text-red-400'}>
                    {health?.status || 'Unknown'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1">
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
              {activeTab === 'general' && (
                <div>
                  <h2 className="text-lg font-semibold mb-6">General Settings</h2>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Default Android Version
                      </label>
                      <select className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500">
                        <option value="14">Android 14</option>
                        <option value="13">Android 13</option>
                        <option value="12">Android 12</option>
                        <option value="11">Android 11</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Default Screen Resolution
                      </label>
                      <select className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500">
                        <option value="1080x2400">1080 x 2400 (FHD+)</option>
                        <option value="1440x3200">1440 x 3200 (QHD+)</option>
                        <option value="720x1600">720 x 1600 (HD+)</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="block text-sm font-medium">
                          Auto-refresh profiles
                        </label>
                        <p className="text-sm text-gray-400">
                          Automatically refresh profile status every 5 seconds
                        </p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary-600">
                        <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'api' && (
                <div>
                  <h2 className="text-lg font-semibold mb-6">API Keys</h2>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Anthropic API Key
                      </label>
                      <input
                        type="password"
                        placeholder="sk-ant-..."
                        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                      />
                      <p className="mt-1 text-sm text-gray-400">
                        Required for AI-powered automation
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        OpenAI API Key
                      </label>
                      <input
                        type="password"
                        placeholder="sk-..."
                        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                      />
                      <p className="mt-1 text-sm text-gray-400">
                        Optional, for GPT-4 Vision support
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'docker' && (
                <div>
                  <h2 className="text-lg font-semibold mb-6">Docker Settings</h2>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Docker Host
                      </label>
                      <input
                        type="text"
                        defaultValue="unix:///var/run/docker.sock"
                        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Redroid Image
                      </label>
                      <input
                        type="text"
                        defaultValue="redroid/redroid:14.0.0-latest"
                        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Container Memory Limit
                      </label>
                      <select className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500">
                        <option value="2g">2 GB</option>
                        <option value="4g">4 GB</option>
                        <option value="8g">8 GB</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'proxy' && (
                <div>
                  <h2 className="text-lg font-semibold mb-6">Default Proxy Settings</h2>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Proxy Type
                      </label>
                      <select className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500">
                        <option value="none">No Proxy (Direct)</option>
                        <option value="http">HTTP Proxy</option>
                        <option value="socks5">SOCKS5 Proxy</option>
                      </select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          Proxy Host
                        </label>
                        <input
                          type="text"
                          placeholder="proxy.example.com"
                          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">
                          Proxy Port
                        </label>
                        <input
                          type="number"
                          placeholder="8080"
                          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2.5 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div>
                  <h2 className="text-lg font-semibold mb-6">Notifications</h2>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 rounded-lg border border-gray-700">
                      <div>
                        <label className="block text-sm font-medium">
                          Task Completion
                        </label>
                        <p className="text-sm text-gray-400">
                          Notify when an AI task completes
                        </p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary-600">
                        <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between p-4 rounded-lg border border-gray-700">
                      <div>
                        <label className="block text-sm font-medium">
                          Profile Errors
                        </label>
                        <p className="text-sm text-gray-400">
                          Notify when a profile encounters an error
                        </p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-primary-600">
                        <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'appearance' && (
                <div>
                  <h2 className="text-lg font-semibold mb-6">Appearance</h2>
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Theme
                      </label>
                      <div className="grid grid-cols-3 gap-4">
                        <button className="p-4 rounded-lg border-2 border-primary-500 bg-gray-800 text-center">
                          <div className="w-8 h-8 mx-auto mb-2 rounded-full bg-gray-900" />
                          <span className="text-sm">Dark</span>
                        </button>
                        <button className="p-4 rounded-lg border border-gray-700 bg-gray-800 text-center opacity-50">
                          <div className="w-8 h-8 mx-auto mb-2 rounded-full bg-white" />
                          <span className="text-sm">Light</span>
                        </button>
                        <button className="p-4 rounded-lg border border-gray-700 bg-gray-800 text-center opacity-50">
                          <div className="w-8 h-8 mx-auto mb-2 rounded-full bg-gradient-to-b from-white to-gray-900" />
                          <span className="text-sm">System</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Save button */}
              <div className="mt-8 flex justify-end gap-4">
                <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-700 text-gray-400 hover:bg-gray-800 transition-colors">
                  <RefreshCw className="h-4 w-4" />
                  Reset
                </button>
                <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors">
                  <Save className="h-4 w-4" />
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

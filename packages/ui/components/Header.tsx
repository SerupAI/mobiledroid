'use client';

import Link from 'next/link';
import { Smartphone, Settings, LayoutDashboard, History, Camera, ListTodo, Globe } from 'lucide-react';

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-900/95 backdrop-blur">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Smartphone className="h-6 w-6 text-primary-500" />
            <span className="text-xl font-bold">MobileDroid</span>
          </Link>

          <nav className="flex items-center gap-6">
            <Link
              href="/"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <LayoutDashboard className="h-4 w-4" />
              <span>Dashboard</span>
            </Link>
            <Link
              href="/profiles"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <Smartphone className="h-4 w-4" />
              <span>Profiles</span>
            </Link>
            <Link
              href="/history"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <History className="h-4 w-4" />
              <span>History</span>
            </Link>
            <Link
              href="/snapshots"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <Camera className="h-4 w-4" />
              <span>Snapshots</span>
            </Link>
            <Link
              href="/tasks"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <ListTodo className="h-4 w-4" />
              <span>Tasks</span>
            </Link>
            <Link
              href="/proxies"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <Globe className="h-4 w-4" />
              <span>Proxies</span>
            </Link>
            <Link
              href="/settings"
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <Settings className="h-4 w-4" />
              <span>Settings</span>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}

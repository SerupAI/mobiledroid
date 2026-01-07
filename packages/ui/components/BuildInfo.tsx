'use client';

import { useBuildInfo } from '@/hooks/useBuildInfo';

export function BuildInfo() {
  const buildInfo = useBuildInfo();

  // Only show in debug mode
  if (process.env.NEXT_PUBLIC_DEBUG !== 'true' || !buildInfo) {
    return null;
  }

  return (
    <div className="fixed bottom-2 left-2 text-xs text-gray-600 bg-gray-900/80 px-2 py-1 rounded-md font-mono">
      <span className="text-gray-500">commit:</span> {buildInfo.commitSha}
      <span className="text-gray-700 mx-1">•</span>
      <span className="text-gray-500">built:</span> {new Date(buildInfo.buildTime).toLocaleTimeString()}
    </div>
  );
}
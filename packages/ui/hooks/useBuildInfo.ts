import { useState, useEffect } from 'react';

interface BuildInfo {
  commitSha: string;
  buildTime: string;
  version: string;
}

export function useBuildInfo() {
  const [buildInfo, setBuildInfo] = useState<BuildInfo | null>(null);

  useEffect(() => {
    // Only fetch in debug mode
    if (process.env.NEXT_PUBLIC_DEBUG !== 'true') {
      return;
    }

    fetch('/build-info.json')
      .then(res => res.json())
      .then(data => setBuildInfo(data))
      .catch(err => console.error('Failed to load build info:', err));
  }, []);

  return buildInfo;
}
'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Loader2, MonitorOff, Server, Wifi, Monitor } from 'lucide-react';
import { api } from '@/lib/api';

interface DeviceViewerProps {
  profileId: string;
  onTap?: (x: number, y: number) => void;
}

export function DeviceViewer({ profileId, onTap }: DeviceViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [isImageLoading, setIsImageLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  const [imageKey, setImageKey] = useState(0);

  // Poll device readiness
  const { data: readiness } = useQuery({
    queryKey: ['device-ready', profileId],
    queryFn: () => api.checkDeviceReady(profileId),
    refetchInterval: (query) => {
      // Poll faster while not ready, slower once ready
      return query.state.data?.ready ? 5000 : 2000;
    },
  });

  const isReady = readiness?.ready ?? false;

  // Only refresh screenshot when device is ready
  useEffect(() => {
    if (!isReady) return;

    const interval = setInterval(() => {
      setImageKey((k) => k + 1);
    }, 2000);

    return () => clearInterval(interval);
  }, [isReady]);

  const refreshScreenshot = () => {
    setImageKey((k) => k + 1);
    setIsImageLoading(true);
    setImageError(false);
  };

  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !onTap || !isReady) return;

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    onTap(x, y);
  };

  const handleImageLoad = () => {
    setIsImageLoading(false);
    setImageError(false);
  };

  const handleImageError = () => {
    setIsImageLoading(false);
    setImageError(true);
  };

  // Render boot progress
  const renderBootProgress = () => {
    if (!readiness) {
      return (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95 z-10">
          <Loader2 className="h-10 w-10 animate-spin text-primary-500 mb-4" />
          <p className="text-sm text-gray-300">Checking device status...</p>
        </div>
      );
    }

    const steps = [
      { key: 'container', label: 'Container', done: readiness.container_running, icon: Server },
      { key: 'adb', label: 'ADB', done: readiness.adb_connected, icon: Wifi },
      { key: 'screen', label: 'Screen', done: readiness.screen_available, icon: Monitor },
    ];

    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95 z-10">
        <Loader2 className="h-10 w-10 animate-spin text-primary-500 mb-4" />
        <p className="text-sm text-gray-300 mb-2">{readiness.message}</p>

        <div className="flex items-center gap-4 mt-4">
          {steps.map((step) => (
            <div key={step.key} className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step.done
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-gray-800 text-gray-500'
                }`}
              >
                <step.icon className="h-5 w-5" />
              </div>
              <span className={`text-xs mt-1 ${step.done ? 'text-green-400' : 'text-gray-500'}`}>
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="relative" ref={containerRef}>
      {/* Refresh button - only show when ready */}
      {isReady && (
        <button
          onClick={refreshScreenshot}
          className="absolute top-2 right-2 z-10 rounded-full bg-gray-800/80 p-2 text-gray-400 hover:text-white transition-colors"
          title="Refresh screenshot"
        >
          <RefreshCw className={`h-4 w-4 ${isImageLoading ? 'animate-spin' : ''}`} />
        </button>
      )}

      {/* Device screen container */}
      <div className="aspect-phone bg-black rounded-lg overflow-hidden relative">
        {/* Not ready - show boot progress */}
        {!isReady && renderBootProgress()}

        {/* Ready - show loading overlay while image loads */}
        {isReady && isImageLoading && !imageError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 z-10">
            <Loader2 className="h-8 w-8 animate-spin text-primary-500 mb-2" />
            <p className="text-sm text-gray-400">Loading screen...</p>
          </div>
        )}

        {/* Ready but image error */}
        {isReady && imageError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95 z-10">
            <MonitorOff className="h-12 w-12 text-gray-600 mb-3" />
            <p className="text-sm text-gray-400 mb-4">Screenshot failed</p>
            <button
              onClick={refreshScreenshot}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-md text-sm font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Actual screenshot image - only render when ready */}
        {isReady && (
          <img
            ref={imgRef}
            key={imageKey}
            src={`${api.getScreenshotUrl(profileId)}?t=${imageKey}`}
            alt="Device screen"
            className={`w-full h-full object-contain cursor-pointer ${imageError ? 'opacity-0' : ''}`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            onClick={handleClick}
            draggable={false}
          />
        )}
      </div>
    </div>
  );
}

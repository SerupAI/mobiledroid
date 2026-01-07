/**
 * @jest-environment jsdom
 */

describe('ApiClient', () => {
  const mockFetch = global.fetch as jest.Mock;
  const API_URL = 'http://localhost:8000';

  beforeEach(() => {
    jest.resetModules();
    mockFetch.mockReset();
  });

  describe('getProfiles', () => {
    it('should fetch profiles successfully', async () => {
      const mockProfiles = {
        profiles: [
          {
            id: '1',
            name: 'Test Profile',
            status: 'stopped',
            container_id: null,
            adb_port: null,
            fingerprint: {
              model: 'Pixel 7',
              brand: 'google',
              manufacturer: 'Google',
              build_fingerprint: 'google/panther/panther:14/...',
              android_version: '14',
              sdk_version: '34',
              screen: { width: 1080, height: 2400, dpi: 420 },
            },
            proxy: { type: 'none', host: null, port: null, username: null, password: null },
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            last_started_at: null,
            last_stopped_at: null,
          },
        ],
        total: 1,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles,
      });

      const { api } = await import('@/lib/api');
      const result = await api.getProfiles();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles'),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' },
        })
      );
      expect(result).toEqual(mockProfiles);
    });

    it('should handle fetch error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      const { api } = await import('@/lib/api');

      await expect(api.getProfiles()).rejects.toThrow('Internal server error');
    });
  });

  describe('createProfile', () => {
    it('should create a profile successfully', async () => {
      const mockProfile = {
        id: '1',
        name: 'New Profile',
        status: 'stopped',
        container_id: null,
        adb_port: null,
        fingerprint: {
          model: 'Pixel 7',
          brand: 'google',
          manufacturer: 'Google',
          build_fingerprint: 'google/panther/panther:14/...',
          android_version: '14',
          sdk_version: '34',
          screen: { width: 1080, height: 2400, dpi: 420 },
        },
        proxy: { type: 'none', host: null, port: null, username: null, password: null },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        last_started_at: null,
        last_stopped_at: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile,
      });

      const { api } = await import('@/lib/api');
      const result = await api.createProfile({
        name: 'New Profile',
        fingerprint: {
          model: 'Pixel 7',
          brand: 'google',
          manufacturer: 'Google',
          build_fingerprint: 'google/panther/panther:14/...',
          android_version: '14',
          sdk_version: '34',
          screen: { width: 1080, height: 2400, dpi: 420 },
        },
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.any(String),
        })
      );
      expect(result).toEqual(mockProfile);
    });
  });

  describe('startProfile', () => {
    it('should start a profile successfully', async () => {
      const mockProfile = {
        id: '1',
        name: 'Test Profile',
        status: 'running',
        container_id: 'container-123',
        adb_port: 5555,
        fingerprint: {
          model: 'Pixel 7',
          brand: 'google',
          manufacturer: 'Google',
          build_fingerprint: 'google/panther/panther:14/...',
          android_version: '14',
          sdk_version: '34',
          screen: { width: 1080, height: 2400, dpi: 420 },
        },
        proxy: { type: 'none', host: null, port: null, username: null, password: null },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        last_started_at: '2024-01-01T01:00:00Z',
        last_stopped_at: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile,
      });

      const { api } = await import('@/lib/api');
      const result = await api.startProfile('1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles/1/start'),
        expect.objectContaining({
          method: 'POST',
        })
      );
      expect(result.status).toBe('running');
    });
  });

  describe('stopProfile', () => {
    it('should stop a profile successfully', async () => {
      const mockProfile = {
        id: '1',
        name: 'Test Profile',
        status: 'stopped',
        container_id: null,
        adb_port: null,
        fingerprint: {
          model: 'Pixel 7',
          brand: 'google',
          manufacturer: 'Google',
          build_fingerprint: 'google/panther/panther:14/...',
          android_version: '14',
          sdk_version: '34',
          screen: { width: 1080, height: 2400, dpi: 420 },
        },
        proxy: { type: 'none', host: null, port: null, username: null, password: null },
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        last_started_at: '2024-01-01T01:00:00Z',
        last_stopped_at: '2024-01-01T02:00:00Z',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile,
      });

      const { api } = await import('@/lib/api');
      const result = await api.stopProfile('1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles/1/stop'),
        expect.objectContaining({
          method: 'POST',
        })
      );
      expect(result.status).toBe('stopped');
    });
  });

  describe('deleteProfile', () => {
    it('should delete a profile successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      const { api } = await import('@/lib/api');
      await api.deleteProfile('1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/profiles/1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('getHealth', () => {
    it('should fetch health status', async () => {
      const mockHealth = { status: 'healthy', version: '0.1.0' };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHealth,
      });

      const { api } = await import('@/lib/api');
      const result = await api.getHealth();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/health'),
        expect.any(Object)
      );
      expect(result).toEqual(mockHealth);
    });
  });
});

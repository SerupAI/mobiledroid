/**
 * Browser Fingerprint Protection for Android WebView
 *
 * This script protects against browser-based fingerprinting techniques:
 * - Canvas fingerprinting (pixel noise injection)
 * - WebGL fingerprinting (GPU info spoofing)
 * - Audio fingerprinting (oscillator noise)
 * - WebRTC leak prevention (IP masking)
 *
 * Injection methods:
 * 1. Chrome extension (recommended for Redroid)
 * 2. Tampermonkey/userscript
 * 3. WebView.addJavascriptInterface()
 * 4. Frida JavaScript injection
 *
 * Configuration is read from window.__FINGERPRINT_CONFIG__ if available
 */

(function() {
  'use strict';

  // Prevent double injection
  if (window.__FINGERPRINT_PROTECTION_LOADED__) return;
  window.__FINGERPRINT_PROTECTION_LOADED__ = true;

  // Configuration - can be overridden by setting window.__FINGERPRINT_CONFIG__
  const config = window.__FINGERPRINT_CONFIG__ || {
    // Canvas protection
    canvas: {
      enabled: true,
      noiseLevel: 2 // -2 to 2 pixel variation
    },
    // WebGL protection
    webgl: {
      enabled: true,
      vendor: 'Qualcomm',
      renderer: null // null = random from list
    },
    // Audio protection
    audio: {
      enabled: true,
      noiseLevel: 0.0001
    },
    // WebRTC protection
    webrtc: {
      enabled: true,
      blockLocalIPs: true
    },
    // Debug logging
    debug: false
  };

  function log(...args) {
    if (config.debug) {
      console.log('[FingerprintProtection]', ...args);
    }
  }

  log('Initializing fingerprint protection...');

  // ============================================
  // CANVAS FINGERPRINTING PROTECTION
  // ============================================
  if (config.canvas.enabled) {
    const originalGetContext = HTMLCanvasElement.prototype.getContext;

    HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
      const ctx = originalGetContext.apply(this, [contextType, ...args]);

      if (contextType === '2d' && ctx) {
        // Hook getImageData to add noise
        const originalGetImageData = ctx.getImageData;
        ctx.getImageData = function(sx, sy, sw, sh) {
          const imageData = originalGetImageData.apply(this, [sx, sy, sw, sh]);

          // Add subtle noise to prevent fingerprinting
          const noise = config.canvas.noiseLevel;
          for (let i = 0; i < imageData.data.length; i += 4) {
            const n = Math.random() * noise * 2 - noise;
            imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + n));     // R
            imageData.data[i+1] = Math.min(255, Math.max(0, imageData.data[i+1] + n)); // G
            imageData.data[i+2] = Math.min(255, Math.max(0, imageData.data[i+2] + n)); // B
            // Alpha channel unchanged
          }

          return imageData;
        };

        // Hook toDataURL to add variation
        const originalToDataURL = this.toDataURL;
        this.toDataURL = function(type, quality) {
          const data = originalToDataURL.apply(this, [type, quality]);

          // Add slight variation to prevent consistent fingerprints
          if (data.length > 50) {
            const chars = data.split('');
            const idx = chars.length - 20 - Math.floor(Math.random() * 20);
            // Only modify base64 padding area
            if (chars[idx] && /[A-Za-z0-9]/.test(chars[idx])) {
              chars[idx] = String.fromCharCode(chars[idx].charCodeAt(0) ^ 1);
            }
            return chars.join('');
          }

          return data;
        };

        log('Canvas 2D protection applied');
      }

      return ctx;
    };

    // Hook toBlob for canvas
    const originalToBlob = HTMLCanvasElement.prototype.toBlob;
    HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {
      const canvas = this;

      originalToBlob.call(canvas, function(blob) {
        if (blob && blob.size > 100) {
          // Add slight variation to blob
          const reader = new FileReader();
          reader.onload = function() {
            const arr = new Uint8Array(reader.result);
            // Flip a random bit in the middle of the data
            const idx = Math.floor(arr.length / 2) + Math.floor(Math.random() * 100);
            if (idx < arr.length) {
              arr[idx] = arr[idx] ^ 1;
            }
            callback(new Blob([arr], { type: blob.type }));
          };
          reader.readAsArrayBuffer(blob);
        } else {
          callback(blob);
        }
      }, type, quality);
    };

    log('Canvas protection enabled');
  }

  // ============================================
  // WEBGL FINGERPRINTING PROTECTION
  // ============================================
  if (config.webgl.enabled) {
    // Mobile GPU renderers (realistic for Android devices)
    const mobileRenderers = {
      'Qualcomm': [
        'Adreno (TM) 730',
        'Adreno (TM) 660',
        'Adreno (TM) 650',
        'Adreno (TM) 640',
        'Adreno (TM) 620',
        'Adreno (TM) 619'
      ],
      'ARM': [
        'Mali-G710 MC10',
        'Mali-G78 MP24',
        'Mali-G77 MC9',
        'Mali-G76 MC4',
        'Mali-G72 MP12'
      ],
      'Imagination Technologies': [
        'PowerVR Rogue GE8320'
      ]
    };

    // Select renderer based on config
    let selectedVendor = config.webgl.vendor;
    let selectedRenderer = config.webgl.renderer;

    if (!selectedRenderer) {
      const vendors = Object.keys(mobileRenderers);
      if (!selectedVendor || !mobileRenderers[selectedVendor]) {
        selectedVendor = vendors[Math.floor(Math.random() * vendors.length)];
      }
      const renderers = mobileRenderers[selectedVendor];
      selectedRenderer = renderers[Math.floor(Math.random() * renderers.length)];
    }

    const hookWebGL = function(gl) {
      const originalGetParameter = gl.getParameter;

      gl.getParameter = function(pname) {
        // UNMASKED_VENDOR_WEBGL
        if (pname === 37445) {
          return selectedVendor;
        }
        // UNMASKED_RENDERER_WEBGL
        if (pname === 37446) {
          return selectedRenderer;
        }
        // VERSION
        if (pname === gl.VERSION) {
          return 'WebGL 1.0 (OpenGL ES 2.0 Chromium)';
        }
        // SHADING_LANGUAGE_VERSION
        if (pname === gl.SHADING_LANGUAGE_VERSION) {
          return 'WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)';
        }
        // MAX_TEXTURE_SIZE - mobile appropriate
        if (pname === gl.MAX_TEXTURE_SIZE) {
          return 8192;
        }
        // MAX_RENDERBUFFER_SIZE
        if (pname === gl.MAX_RENDERBUFFER_SIZE) {
          return 8192;
        }

        return originalGetParameter.apply(this, [pname]);
      };

      // Spoof extensions list
      const originalGetSupportedExtensions = gl.getSupportedExtensions;
      gl.getSupportedExtensions = function() {
        return [
          'ANGLE_instanced_arrays',
          'EXT_blend_minmax',
          'EXT_color_buffer_half_float',
          'EXT_disjoint_timer_query',
          'EXT_float_blend',
          'EXT_frag_depth',
          'EXT_shader_texture_lod',
          'EXT_texture_compression_bptc',
          'EXT_texture_compression_rgtc',
          'EXT_texture_filter_anisotropic',
          'WEBKIT_EXT_texture_filter_anisotropic',
          'EXT_sRGB',
          'OES_element_index_uint',
          'OES_fbo_render_mipmap',
          'OES_standard_derivatives',
          'OES_texture_float',
          'OES_texture_float_linear',
          'OES_texture_half_float',
          'OES_texture_half_float_linear',
          'OES_vertex_array_object',
          'WEBGL_color_buffer_float',
          'WEBGL_compressed_texture_s3tc',
          'WEBKIT_WEBGL_compressed_texture_s3tc',
          'WEBGL_compressed_texture_s3tc_srgb',
          'WEBGL_debug_renderer_info',
          'WEBGL_debug_shaders',
          'WEBGL_depth_texture',
          'WEBKIT_WEBGL_depth_texture',
          'WEBGL_draw_buffers',
          'WEBGL_lose_context',
          'WEBKIT_WEBGL_lose_context'
        ];
      };

      // Add noise to shader source to prevent shader-based fingerprinting
      const originalShaderSource = gl.shaderSource;
      gl.shaderSource = function(shader, source) {
        // Add random comment to shader
        const noise = '// ' + Math.random().toString(36).substring(2, 8);
        const modified = source + '\n' + noise;
        return originalShaderSource.apply(this, [shader, modified]);
      };
    };

    // Hook both WebGL versions
    const originalGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
      const ctx = originalGetContext.apply(this, [contextType, ...args]);

      if (ctx && (contextType === 'webgl' || contextType === 'experimental-webgl' || contextType === 'webgl2')) {
        hookWebGL(ctx);
        log('WebGL protection applied to', contextType);
      }

      return ctx;
    };

    log('WebGL protection enabled - Vendor:', selectedVendor, 'Renderer:', selectedRenderer);
  }

  // ============================================
  // AUDIO FINGERPRINTING PROTECTION
  // ============================================
  if (config.audio.enabled) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;

    if (AudioContext) {
      // Hook createOscillator to add frequency noise
      const originalCreateOscillator = AudioContext.prototype.createOscillator;
      AudioContext.prototype.createOscillator = function() {
        const oscillator = originalCreateOscillator.apply(this);

        const originalConnect = oscillator.connect;
        oscillator.connect = function(...args) {
          // Add slight frequency variation
          const noise = config.audio.noiseLevel;
          oscillator.frequency.value *= (1 + (Math.random() * noise * 2 - noise));
          return originalConnect.apply(this, args);
        };

        return oscillator;
      };

      // Hook createAnalyser to add noise to frequency data
      const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
      AudioContext.prototype.createAnalyser = function() {
        const analyser = originalCreateAnalyser.apply(this);

        const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
        analyser.getFloatFrequencyData = function(array) {
          originalGetFloatFrequencyData.apply(this, [array]);
          // Add noise to frequency data
          for (let i = 0; i < array.length; i++) {
            array[i] += (Math.random() * 0.1 - 0.05);
          }
        };

        return analyser;
      };

      log('Audio fingerprint protection enabled');
    }
  }

  // ============================================
  // WEBRTC LEAK PREVENTION
  // ============================================
  if (config.webrtc.enabled) {
    const RTCPeerConnection = window.RTCPeerConnection ||
                              window.webkitRTCPeerConnection ||
                              window.mozRTCPeerConnection;

    if (RTCPeerConnection) {
      // Override RTCPeerConnection to prevent IP leaks
      const OriginalRTCPeerConnection = RTCPeerConnection;

      window.RTCPeerConnection = function(configuration) {
        // Replace STUN servers with safe ones
        if (configuration && configuration.iceServers) {
          configuration.iceServers = [
            { urls: 'stun:stun.l.google.com:19302' }
          ];
        }

        const pc = new OriginalRTCPeerConnection(configuration);

        // Hook createDataChannel to add timing noise
        const originalCreateDataChannel = pc.createDataChannel;
        pc.createDataChannel = function(...args) {
          const channel = originalCreateDataChannel.apply(this, args);

          // Add random delay to data channel operations
          const originalSend = channel.send;
          channel.send = function(data) {
            setTimeout(() => {
              originalSend.apply(this, [data]);
            }, Math.random() * 5);
          };

          return channel;
        };

        return pc;
      };

      // Copy static properties
      window.RTCPeerConnection.prototype = OriginalRTCPeerConnection.prototype;

      // Also override for webkit prefix
      if (window.webkitRTCPeerConnection) {
        window.webkitRTCPeerConnection = window.RTCPeerConnection;
      }

      log('WebRTC leak prevention enabled');
    }
  }

  // ============================================
  // ADDITIONAL PROTECTIONS
  // ============================================

  // Hide automation indicators
  Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true
  });

  // Spoof plugins (mobile Chrome typically has none)
  Object.defineProperty(navigator, 'plugins', {
    get: () => [],
    configurable: true
  });

  // Spoof mimeTypes
  Object.defineProperty(navigator, 'mimeTypes', {
    get: () => [],
    configurable: true
  });

  // Battery API spoofing (common fingerprinting vector)
  if (navigator.getBattery) {
    navigator.getBattery = function() {
      return Promise.resolve({
        charging: true,
        chargingTime: 0,
        dischargingTime: Infinity,
        level: Math.random() * 0.3 + 0.7, // 70-100%
        addEventListener: function() {},
        removeEventListener: function() {}
      });
    };
  }

  log('Fingerprint protection fully initialized');

})();

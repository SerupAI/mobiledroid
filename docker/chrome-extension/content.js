/**
 * Content script that injects fingerprint protection into the page context
 * This runs before any page scripts execute
 */

(function() {
  'use strict';

  // Read configuration from localStorage if available
  // This allows the Android app to configure protection per-profile
  let config = null;
  try {
    const stored = localStorage.getItem('__FINGERPRINT_CONFIG__');
    if (stored) {
      config = JSON.parse(stored);
    }
  } catch (e) {
    // Ignore errors
  }

  // Inject the protection script into the page context
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL('inject.js');

  // Pass configuration to the injected script
  if (config) {
    const configScript = document.createElement('script');
    configScript.textContent = 'window.__FINGERPRINT_CONFIG__ = ' + JSON.stringify(config) + ';';
    (document.head || document.documentElement).appendChild(configScript);
    configScript.remove();
  }

  // Inject as early as possible
  (document.head || document.documentElement).appendChild(script);
  script.onload = function() {
    script.remove();
  };
})();

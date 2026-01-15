#!/system/bin/sh
# install-fingerprint-extension.sh
# Installs the fingerprint protection Chrome extension in Redroid
#
# This script should be run after the container boots to install
# the browser fingerprint protection extension.

LOG_TAG="ExtensionInstaller"
EXTENSION_DIR="/data/local/chrome-extension"
CHROME_PREFS_DIR="/data/data/com.android.chrome/app_chrome/Default"

log_info() {
    echo "[$LOG_TAG] $1"
}

log_error() {
    echo "[$LOG_TAG] ERROR: $1" >&2
}

# Check if extension files exist
if [ ! -d "$EXTENSION_DIR" ]; then
    log_error "Extension directory not found: $EXTENSION_DIR"
    log_info "Please mount the chrome-extension directory to $EXTENSION_DIR"
    exit 1
fi

# Verify required files
for file in manifest.json content.js inject.js; do
    if [ ! -f "$EXTENSION_DIR/$file" ]; then
        log_error "Missing required file: $file"
        exit 1
    fi
done

log_info "Extension files verified"

# Create Chrome policies directory for extension installation
POLICIES_DIR="/data/local/chrome-policies"
mkdir -p "$POLICIES_DIR"

# Create policy to force-install the extension
# Note: This requires the extension to be loaded as an unpacked extension
# For Redroid, we use command-line flags instead

log_info "Extension installation configured"

# Set configuration based on environment variables
if [ -n "$WEBGL_VENDOR" ] || [ -n "$WEBGL_RENDERER" ]; then
    log_info "Creating fingerprint configuration..."

    # Create configuration file that the extension will read
    CONFIG_FILE="$EXTENSION_DIR/config.json"
    cat > "$CONFIG_FILE" << EOF
{
  "canvas": {
    "enabled": true,
    "noiseLevel": ${CANVAS_NOISE_LEVEL:-2}
  },
  "webgl": {
    "enabled": true,
    "vendor": "${WEBGL_VENDOR:-Qualcomm}",
    "renderer": "${WEBGL_RENDERER:-}"
  },
  "audio": {
    "enabled": true,
    "noiseLevel": 0.0001
  },
  "webrtc": {
    "enabled": true,
    "blockLocalIPs": true
  },
  "debug": ${DEBUG:-false}
}
EOF
    log_info "Configuration written to $CONFIG_FILE"
fi

log_info "Fingerprint extension installation complete"
log_info ""
log_info "To use the extension, start Chrome with:"
log_info "  --load-extension=$EXTENSION_DIR"
log_info ""
log_info "Or use the provided launch script."

exit 0

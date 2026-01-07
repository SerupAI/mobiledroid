#!/bin/bash
# entrypoint.sh
# Custom entrypoint for MobileDroid redroid containers
# Handles fingerprint injection and redroid initialization

set -e

LOG_PREFIX="[MobileDroid]"

log_info() {
    echo "$LOG_PREFIX $1"
}

log_error() {
    echo "$LOG_PREFIX ERROR: $1" >&2
}

# Ensure scripts are executable
chmod +x /system/bin/inject-fingerprint.sh 2>/dev/null || true

# Log startup configuration
log_info "Starting MobileDroid redroid container"
log_info "Device: $DEVICE_BRAND $DEVICE_MODEL"
log_info "Android: $ANDROID_VERSION (SDK $SDK_VERSION)"
log_info "Screen: ${DEVICE_WIDTH}x${DEVICE_HEIGHT} @ ${DEVICE_DPI}dpi"

# Build redroid command with fingerprint-related options
REDROID_ARGS=""

# GPU settings (prefer hardware acceleration if available)
if [ -e /dev/dri ]; then
    log_info "GPU detected, enabling hardware acceleration"
    REDROID_ARGS="$REDROID_ARGS androidboot.redroid_gpu_mode=host"
else
    log_info "No GPU detected, using software rendering"
    REDROID_ARGS="$REDROID_ARGS androidboot.redroid_gpu_mode=guest"
fi

# Screen dimensions
REDROID_ARGS="$REDROID_ARGS androidboot.redroid_width=$DEVICE_WIDTH"
REDROID_ARGS="$REDROID_ARGS androidboot.redroid_height=$DEVICE_HEIGHT"
REDROID_ARGS="$REDROID_ARGS androidboot.redroid_dpi=$DEVICE_DPI"

# FPS setting (30 is smooth enough for automation)
REDROID_ARGS="$REDROID_ARGS androidboot.redroid_fps=30"

# Proxy configuration if provided
if [ -n "$PROXY_HOST" ] && [ -n "$PROXY_PORT" ]; then
    log_info "Configuring proxy: $PROXY_HOST:$PROXY_PORT"
    REDROID_ARGS="$REDROID_ARGS androidboot.redroid_net_proxy_host=$PROXY_HOST"
    REDROID_ARGS="$REDROID_ARGS androidboot.redroid_net_proxy_port=$PROXY_PORT"

    if [ -n "$PROXY_USERNAME" ] && [ -n "$PROXY_PASSWORD" ]; then
        REDROID_ARGS="$REDROID_ARGS androidboot.redroid_net_proxy_username=$PROXY_USERNAME"
        REDROID_ARGS="$REDROID_ARGS androidboot.redroid_net_proxy_password=$PROXY_PASSWORD"
    fi
fi

# Additional redroid options
REDROID_ARGS="$REDROID_ARGS androidboot.redroid_net_ndns=8.8.8.8"

# Export properties for fingerprint injection to read
export DEVICE_MODEL DEVICE_BRAND DEVICE_MANUFACTURER DEVICE_PRODUCT
export BUILD_FINGERPRINT ANDROID_ID DEVICE_SERIAL
export DEVICE_WIDTH DEVICE_HEIGHT DEVICE_DPI
export SDK_VERSION ANDROID_VERSION HARDWARE BOARD
export TIMEZONE LOCALE

# Create a properties file that can be read by the Android system
PROPS_FILE="/data/local/tmp/mobiledroid_props.sh"
mkdir -p /data/local/tmp 2>/dev/null || true
cat > "$PROPS_FILE" << EOF
DEVICE_MODEL="$DEVICE_MODEL"
DEVICE_BRAND="$DEVICE_BRAND"
DEVICE_MANUFACTURER="$DEVICE_MANUFACTURER"
DEVICE_PRODUCT="$DEVICE_PRODUCT"
BUILD_FINGERPRINT="$BUILD_FINGERPRINT"
ANDROID_ID="$ANDROID_ID"
DEVICE_SERIAL="$DEVICE_SERIAL"
SDK_VERSION="$SDK_VERSION"
ANDROID_VERSION="$ANDROID_VERSION"
HARDWARE="$HARDWARE"
BOARD="$BOARD"
EOF

log_info "Starting redroid with args: $REDROID_ARGS"

# Execute the original redroid init
# The redroid image uses /init as the entry point
exec /init $REDROID_ARGS "$@"

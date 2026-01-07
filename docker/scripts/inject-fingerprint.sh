#!/system/bin/sh
# inject-fingerprint.sh
# This script modifies Android system properties to spoof device fingerprint
# It runs before Android services fully initialize

LOG_TAG="FingerprintInjector"

log_info() {
    echo "[$LOG_TAG] $1"
}

log_error() {
    echo "[$LOG_TAG] ERROR: $1" >&2
}

# Function to set a system property safely
set_prop() {
    local prop_name="$1"
    local prop_value="$2"

    if [ -n "$prop_value" ]; then
        setprop "$prop_name" "$prop_value" 2>/dev/null
        if [ $? -eq 0 ]; then
            log_info "Set $prop_name"
        else
            log_error "Failed to set $prop_name"
        fi
    fi
}

# Generate random Android ID if not provided
generate_android_id() {
    if [ -z "$ANDROID_ID" ]; then
        # Generate a random 16-character hex string
        ANDROID_ID=$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 16 | head -n 1)
        log_info "Generated Android ID: $ANDROID_ID"
    fi
}

# Generate random serial if not provided
generate_serial() {
    if [ -z "$DEVICE_SERIAL" ]; then
        # Generate a random serial number
        DEVICE_SERIAL=$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 12 | head -n 1)
        log_info "Generated Serial: $DEVICE_SERIAL"
    fi
}

# Main fingerprint injection
inject_fingerprint() {
    log_info "Starting fingerprint injection..."

    # Generate IDs if needed
    generate_android_id
    generate_serial

    # Device identification properties
    set_prop "ro.product.model" "$DEVICE_MODEL"
    set_prop "ro.product.brand" "$DEVICE_BRAND"
    set_prop "ro.product.manufacturer" "$DEVICE_MANUFACTURER"
    set_prop "ro.product.name" "$DEVICE_PRODUCT"
    set_prop "ro.product.device" "$DEVICE_PRODUCT"

    # Build fingerprint
    set_prop "ro.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.bootimage.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.system.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.vendor.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.odm.build.fingerprint" "$BUILD_FINGERPRINT"

    # Build info
    set_prop "ro.build.version.sdk" "$SDK_VERSION"
    set_prop "ro.build.version.release" "$ANDROID_VERSION"
    set_prop "ro.build.version.release_or_codename" "$ANDROID_VERSION"

    # Hardware info
    set_prop "ro.hardware" "$HARDWARE"
    set_prop "ro.product.board" "$BOARD"
    set_prop "ro.board.platform" "$BOARD"

    # Serial number
    set_prop "ro.serialno" "$DEVICE_SERIAL"
    set_prop "ro.boot.serialno" "$DEVICE_SERIAL"

    # Display properties
    set_prop "ro.sf.lcd_density" "$DEVICE_DPI"

    # Timezone and locale
    if [ -n "$TIMEZONE" ]; then
        set_prop "persist.sys.timezone" "$TIMEZONE"
    fi

    if [ -n "$LOCALE" ]; then
        set_prop "persist.sys.locale" "$LOCALE"
        set_prop "ro.product.locale" "$LOCALE"
    fi

    # Vendor-specific properties based on brand
    case "$DEVICE_BRAND" in
        "samsung")
            set_prop "ro.sec.fle.encryption" "true"
            set_prop "ro.config.knox" "v30"
            ;;
        "google")
            set_prop "ro.com.google.gmsversion" "$ANDROID_VERSION"
            ;;
        "OnePlus")
            set_prop "ro.oxygen.version" "14.0.0"
            ;;
        "Xiaomi"|"Redmi")
            set_prop "ro.miui.ui.version.name" "V14"
            ;;
    esac

    log_info "Fingerprint injection completed"
}

# Execute injection
inject_fingerprint

# Return success
exit 0

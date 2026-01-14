#!/system/bin/sh
# inject-fingerprint.sh
# This script modifies Android system properties to spoof device fingerprint
# It runs before Android services fully initialize
#
# Supports 25+ parameters for comprehensive fingerprint spoofing

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

# Generate WiFi MAC address from prefix
generate_wifi_mac() {
    if [ -n "$WIFI_MAC_PREFIX" ] && [ -z "$WIFI_MAC" ]; then
        # Generate random suffix for MAC
        local suffix=$(cat /dev/urandom | tr -dc 'A-F0-9' | fold -w 6 | head -n 1)
        WIFI_MAC="${WIFI_MAC_PREFIX}:${suffix:0:2}:${suffix:2:2}:${suffix:4:2}"
        log_info "Generated WiFi MAC: $WIFI_MAC"
    fi
}

# Generate Bluetooth MAC address from prefix
generate_bt_mac() {
    if [ -n "$BLUETOOTH_MAC_PREFIX" ] && [ -z "$BLUETOOTH_MAC" ]; then
        # Generate random suffix for MAC
        local suffix=$(cat /dev/urandom | tr -dc 'A-F0-9' | fold -w 6 | head -n 1)
        BLUETOOTH_MAC="${BLUETOOTH_MAC_PREFIX}:${suffix:0:2}:${suffix:2:2}:${suffix:4:2}"
        log_info "Generated Bluetooth MAC: $BLUETOOTH_MAC"
    fi
}

# Main fingerprint injection
inject_fingerprint() {
    log_info "Starting fingerprint injection (25+ parameters)..."

    # Generate IDs if needed
    generate_android_id
    generate_serial
    generate_wifi_mac
    generate_bt_mac

    # ==========================================
    # DEVICE IDENTIFICATION (10 properties)
    # ==========================================
    set_prop "ro.product.model" "$DEVICE_MODEL"
    set_prop "ro.product.brand" "$DEVICE_BRAND"
    set_prop "ro.product.manufacturer" "$DEVICE_MANUFACTURER"
    set_prop "ro.product.name" "$DEVICE_PRODUCT"
    set_prop "ro.product.device" "$DEVICE_NAME"

    # System partitions also need device info
    set_prop "ro.product.system.model" "$DEVICE_MODEL"
    set_prop "ro.product.system.brand" "$DEVICE_BRAND"
    set_prop "ro.product.system.manufacturer" "$DEVICE_MANUFACTURER"
    set_prop "ro.product.vendor.model" "$DEVICE_MODEL"
    set_prop "ro.product.vendor.brand" "$DEVICE_BRAND"

    # ==========================================
    # BUILD FINGERPRINT (6 properties)
    # ==========================================
    set_prop "ro.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.bootimage.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.system.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.vendor.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.odm.build.fingerprint" "$BUILD_FINGERPRINT"
    set_prop "ro.product.build.fingerprint" "$BUILD_FINGERPRINT"

    # ==========================================
    # BUILD INFO (8 properties)
    # ==========================================
    set_prop "ro.build.id" "$BUILD_ID"
    set_prop "ro.build.display.id" "$BUILD_DISPLAY"
    set_prop "ro.build.version.incremental" "$BUILD_INCREMENTAL"
    set_prop "ro.build.type" "$BUILD_TYPE"
    set_prop "ro.build.tags" "$BUILD_TAGS"
    set_prop "ro.build.version.sdk" "$SDK_VERSION"
    set_prop "ro.build.version.release" "$ANDROID_VERSION"
    set_prop "ro.build.version.release_or_codename" "$ANDROID_VERSION"

    # ==========================================
    # HARDWARE INFO (8 properties)
    # ==========================================
    set_prop "ro.hardware" "$HARDWARE"
    set_prop "ro.product.board" "$BOARD"
    set_prop "ro.board.platform" "$PLATFORM"
    set_prop "ro.bootloader" "$BOOTLOADER"
    set_prop "ro.boot.hardware" "$HARDWARE"

    # CPU/ABI info
    set_prop "ro.product.cpu.abi" "$CPU_ABI"
    if [ -n "$SUPPORTED_ABIS" ]; then
        set_prop "ro.product.cpu.abilist" "$SUPPORTED_ABIS"
        set_prop "ro.product.cpu.abilist64" "arm64-v8a"
        set_prop "ro.product.cpu.abilist32" "armeabi-v7a,armeabi"
    fi

    # ==========================================
    # SERIAL NUMBER (3 properties)
    # ==========================================
    set_prop "ro.serialno" "$DEVICE_SERIAL"
    set_prop "ro.boot.serialno" "$DEVICE_SERIAL"
    set_prop "ro.hardware.serial" "$DEVICE_SERIAL"

    # ==========================================
    # DISPLAY PROPERTIES (4 properties)
    # ==========================================
    set_prop "ro.sf.lcd_density" "$DEVICE_DPI"
    set_prop "ro.product.display_size" "${DEVICE_WIDTH}x${DEVICE_HEIGHT}"
    if [ -n "$REFRESH_RATE" ]; then
        set_prop "ro.surface_flinger.max_frame_buffer_acquired_buffers" "3"
        set_prop "ro.surface_flinger.refresh_rate_switching" "true"
    fi

    # ==========================================
    # GRAPHICS / WEBGL (4 properties)
    # ==========================================
    if [ -n "$GL_RENDERER" ]; then
        set_prop "ro.hardware.egl" "mali"  # or adreno
        set_prop "ro.opengles.version" "196610"  # OpenGL ES 3.2
        # Note: WebGL renderer/vendor are typically set at higher level
        # These props help with some detection methods
        set_prop "debug.hwui.renderer" "opengl"
    fi

    # ==========================================
    # NETWORK / MAC ADDRESSES (4 properties)
    # ==========================================
    if [ -n "$WIFI_MAC" ]; then
        set_prop "ro.boot.wifimacaddr" "$WIFI_MAC"
        set_prop "persist.wifi.macaddr" "$WIFI_MAC"
    fi
    if [ -n "$BLUETOOTH_MAC" ]; then
        set_prop "ro.boot.btmacaddr" "$BLUETOOTH_MAC"
        set_prop "persist.bluetooth.macaddr" "$BLUETOOTH_MAC"
    fi

    # ==========================================
    # TIMEZONE AND LOCALE (5 properties)
    # ==========================================
    if [ -n "$TIMEZONE" ]; then
        set_prop "persist.sys.timezone" "$TIMEZONE"
    fi

    if [ -n "$LOCALE" ]; then
        set_prop "persist.sys.locale" "$LOCALE"
        set_prop "ro.product.locale" "$LOCALE"
    fi

    if [ -n "$LANGUAGE" ]; then
        set_prop "persist.sys.language" "$LANGUAGE"
    fi

    if [ -n "$REGION" ]; then
        set_prop "persist.sys.country" "$REGION"
    fi

    # ==========================================
    # VENDOR-SPECIFIC PROPERTIES
    # ==========================================
    case "$DEVICE_BRAND" in
        "samsung"|"Samsung")
            set_prop "ro.sec.fle.encryption" "true"
            set_prop "ro.config.knox" "v30"
            set_prop "ro.product.first_api_level" "$SDK_VERSION"
            set_prop "ro.omc.build.version" "1.0"
            ;;
        "google"|"Google")
            set_prop "ro.com.google.gmsversion" "$ANDROID_VERSION"
            set_prop "ro.product.first_api_level" "$SDK_VERSION"
            set_prop "ro.boot.hardware.revision" "EVT1.0"
            ;;
        "OnePlus")
            set_prop "ro.oxygen.version" "14.0.0"
            set_prop "ro.build.ota.versionname" "$BUILD_DISPLAY"
            ;;
        "Xiaomi"|"Redmi")
            set_prop "ro.miui.ui.version.name" "V14"
            set_prop "ro.miui.ui.version.code" "14"
            set_prop "ro.miui.build.region" "$REGION"
            ;;
        "OPPO")
            set_prop "ro.build.version.opporom" "V14.0"
            set_prop "ro.oppo.market.name" "$DEVICE_MODEL"
            ;;
        "vivo")
            set_prop "ro.vivo.os.version" "14.0"
            set_prop "ro.vivo.market.name" "$DEVICE_MODEL"
            ;;
        "HONOR")
            set_prop "ro.build.version.magic" "8.0.0"
            ;;
        "realme")
            set_prop "ro.build.version.realmeui" "5.0"
            ;;
    esac

    # ==========================================
    # ANTI-EMULATOR DETECTION PROPERTIES
    # ==========================================
    # Make the device appear as a real phone, not an emulator
    set_prop "ro.kernel.qemu" "0"
    set_prop "ro.hardware.virtual" "0"
    set_prop "ro.product.cpu.abilist" "${SUPPORTED_ABIS:-arm64-v8a,armeabi-v7a,armeabi}"
    set_prop "gsm.version.baseband" "1.0"
    set_prop "gsm.version.ril-impl" "android samsung-ril 1.0"

    log_info "Fingerprint injection completed (25+ parameters set)"
}

# Execute injection
inject_fingerprint

# Return success
exit 0

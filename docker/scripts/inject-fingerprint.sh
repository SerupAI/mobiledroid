#!/system/bin/sh
# inject-fingerprint.sh
# This script modifies Android system properties to spoof device fingerprint
# It runs before Android services fully initialize
#
# Supports 30+ parameters for comprehensive fingerprint spoofing
# Architecture-aware: detects ARM vs x86 and applies appropriate measures

LOG_TAG="FingerprintInjector"

log_info() {
    echo "[$LOG_TAG] $1"
}

log_error() {
    echo "[$LOG_TAG] ERROR: $1" >&2
}

# ==========================================
# ARCHITECTURE DETECTION
# ==========================================
# Detect host architecture or use override
# ARCH_MODE can be: auto, arm64, x86_64
detect_architecture() {
    if [ -n "$ARCH_MODE" ] && [ "$ARCH_MODE" != "auto" ]; then
        DETECTED_ARCH="$ARCH_MODE"
        log_info "Architecture override: $DETECTED_ARCH"
    else
        # Detect from uname or CPU info
        local arch=$(uname -m 2>/dev/null || cat /proc/cpuinfo | grep -i "model name" | head -1)
        case "$arch" in
            aarch64|arm64|armv8*)
                DETECTED_ARCH="arm64"
                ;;
            x86_64|i686|i386|AMD*|Intel*)
                DETECTED_ARCH="x86_64"
                ;;
            *)
                # Default to x86 for safety (apply all measures)
                DETECTED_ARCH="x86_64"
                ;;
        esac
        log_info "Detected architecture: $DETECTED_ARCH"
    fi

    # Set flags for conditional features
    if [ "$DETECTED_ARCH" = "arm64" ]; then
        IS_ARM=1
        IS_X86=0
        log_info "Running on ARM - native Android execution, minimal anti-detect needed"
    else
        IS_ARM=0
        IS_X86=1
        log_info "Running on x86 - applying full anti-emulator measures"
    fi
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
    # (x86 only - ARM runs natively, no emulation to hide)
    # ==========================================
    if [ "$IS_X86" = "1" ]; then
        log_info "Applying x86 anti-emulator measures..."

        # Hide QEMU/emulator presence
        set_prop "ro.kernel.qemu" "0"
        set_prop "ro.hardware.virtual" "0"
        set_prop "ro.secure" "1"
        set_prop "ro.debuggable" "0"

        # Hide emulator-specific paths and features
        set_prop "ro.kernel.android.checkjni" "0"
        set_prop "init.svc.qemu-props" "stopped"
        set_prop "qemu.hw.mainkeys" ""

        # Fake baseband/radio (emulators often lack this)
        set_prop "gsm.version.baseband" "1.0"
        set_prop "gsm.version.ril-impl" "android samsung-ril 1.0"
        set_prop "gsm.nitz.time" "$(date +%s)000"

        # Hide goldfish (Android emulator codename)
        set_prop "ro.hardware.audio.primary" "$(echo $HARDWARE | tr '[:upper:]' '[:lower:]')"

        log_info "x86 anti-emulator measures applied"
    else
        log_info "ARM architecture - skipping x86-specific anti-emulator measures"
    fi

    # Common CPU ABI list (both architectures)
    set_prop "ro.product.cpu.abilist" "${SUPPORTED_ABIS:-arm64-v8a,armeabi-v7a,armeabi}"

    # ==========================================
    # P1: GOOGLE SERVICE IDS (2 properties)
    # ==========================================
    # GSF ID (Google Services Framework) - Required for Play Store apps
    if [ -n "$GSF_ID" ]; then
        set_prop "ro.gsf.id" "$GSF_ID"
        log_info "Set GSF ID"
    fi

    # GAID (Google Advertising ID) - Used by ad SDKs
    if [ -n "$GAID" ]; then
        set_prop "persist.google.advertising_id" "$GAID"
        log_info "Set GAID: $GAID"
    fi

    # ==========================================
    # P1: SYSTEM UPTIME SPOOFING (2 properties)
    # ==========================================
    # Spoof boot time to avoid "just booted" detection
    if [ -n "$BOOT_TIME" ]; then
        set_prop "ro.runtime.firstboot" "$BOOT_TIME"
        set_prop "persist.sys.boot_time" "$BOOT_TIME"
        log_info "Set boot time: $BOOT_TIME ($(date -d @$BOOT_TIME 2>/dev/null || echo 'N/A'))"
    fi

    log_info "Fingerprint injection completed (30+ parameters set)"
}

# Detect architecture first
detect_architecture

# Execute injection
inject_fingerprint

# Return success
exit 0

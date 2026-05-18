# HUDDLDOverlaySpike — minimal build

Minimal Android Kotlin proof-of-concept.

## What it does

- Floating draggable bubble ("HUDDLD TEST") over any app
- AccessibilityService logs raw visible text from `com.ubercab.driver`
- MainActivity with overlay/accessibility controls and a log panel

## Build (GitHub Actions — no local Android Studio needed)

Actions → **Build Debug APK** → latest run → Artifacts → **HUDDLDOverlaySpike-debug-apk**

Gradle 8.7 is installed directly in CI. No wrapper files in this repo.

## Setup on device

1. Sideload the APK
2. Open HUDDLD → **Request Overlay Permission** → allow
3. **Open Accessibility Settings** → enable HUDDLD Accessibility
4. **Start Overlay** → purple "HUDDLD TEST" bubble appears
5. Switch to Uber Driver — raw screen text logs in MainActivity

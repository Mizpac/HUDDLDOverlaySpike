# HUDDLDOverlaySpike

A proof-spike Android app that shows a read-only HUDDLD overlay on top of the Uber Driver app.

## What It Does

- Reads visible Uber Eats delivery offer text via AccessibilityService
- Parses pay / distance / estimated minutes
- Calls the HUDDLD Supabase `analyze-offer` endpoint
- Displays **YES / NO / YOUR CALL** in a draggable overlay bubble

---

## Getting the APK (no Android Studio required)

The GitHub Actions workflow builds a debug APK on every push.

1. Go to **Actions → Build Debug APK → latest successful run**
2. Scroll to **Artifacts**
3. Download **HUDDLDOverlaySpike-debug-apk**
4. Unzip and sideload the `.apk` onto your Android device

---

## Step-by-step setup

### 1. Open project in Android Studio (optional)

```
File → Open → select this repo root
```

### 2. Build and install on Android device

Via Android Studio: click **Run**.

Via command line (requires Android SDK):
```bash
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Or download the APK from GitHub Actions artifacts (see above).

### 3. Paste token / apikey / mode / pregameConfig

Open **HUDDLD Overlay** on your device and fill in:

| Field | Example |
|---|---|
| access_token | your Supabase JWT |
| apikey | your Supabase anon/public key |
| mode | `hustle` |
| pregameConfig JSON | `{"targetPerHr":25,"targetPerMile":1.5,"minPay":6,"mpg":28,"gasPrice":3.45,"state":"TX"}` |

Tap **Save Settings**.

### 4. Enable overlay permission

Tap **Request Overlay Permission** → allow in the system dialog.

### 5. Enable HUDDLD accessibility service

Tap **Open Accessibility Settings** → find **HUDDLD Accessibility** → enable it.

### 6. Start overlay

Tap **Start Overlay**. A small HUDDLD bubble appears on screen.

### 7. Open Uber Driver

Switch to the Uber Driver app (`com.ubercab.driver`). The HUDDLD bubble stays on top.

### 8. Confirm HUDDLD bubble appears

The bubble should be visible over Uber Driver.  
If not: check overlay permission (step 4) and that OverlayService is running.

### 9. Confirm raw Uber Driver text appears in logs

Return to HUDDLD Overlay. The debug log panel shows:
```
HH:mm:ss pkg=com.ubercab.driver | raw_len=342 | reads=1
HH:mm:ss RAW_TEXT:
Accept
$9.75
3.4 mi · 16 min
McDonald's
...
```

### 10. Confirm parsed offer data and verdict

When an Uber Eats delivery offer appears in Uber Driver, the log shows:
```
parsed: pay=9.75 dist=3.4 min=16 store=McDonald's
missing=none conf=1.00
parse_success
endpoint: status=200 latency=312ms
endpoint_response: {"verdict":{"verdict":"yes",...},"computed":{"pocket":8.33,...}}
endpoint_success | verdict=YES
```

The overlay bubble updates to **YES** / **NO** / **YOUR CALL**.

---

## Architecture

```
HUDDLDAccessibilityService   ← reads window content from Uber Driver
        │
        ▼
UberDriverExtractionProfile  ← regex parsing (pay, distance, minutes, storeName)
        │
        ▼
SupabaseAnalyzeClient        ← POST analyze-offer
        │                         │
        │                   (fallback on error)
        │                         │
        ▼                         ▼
    OverlayManager          LocalVerdictEngine
        │
        ▼
   Overlay bubble (YES / NO / YOUR CALL)
```

## Endpoint

```
POST https://dccjedwxcaukxhfuumkq.supabase.co/functions/v1/analyze-offer
Authorization: Bearer <access_token>
apikey: <anon_key>
Content-Type: application/json

{
  "source": "manual",
  "pay": 9.75,
  "distance": 3.4,
  "estimatedMinutes": 16,
  "itemCount": null,
  "mode": "hustle",
  "pregameConfig": {
    "targetPerHr": 25,
    "targetPerMile": 1.5,
    "minPay": 6,
    "mpg": 28,
    "gasPrice": 3.45,
    "state": "TX"
  }
}
```

## MediaProjection / OCR fallback

If AccessibilityService exposes no usable text inside Uber Driver (e.g. offer text rendered in a WebView or canvas), the app logs:

```
TODO: MediaProjection + ML Kit OCR fallback – AccessibilityService returned no parseable text from com.ubercab.driver
```

Next milestone: implement `MediaProjectionCaptureService` + ML Kit text recognition.

## Permissions required

| Permission | Why |
|---|---|
| `SYSTEM_ALERT_WINDOW` | Draw overlay bubble over Uber Driver |
| `BIND_ACCESSIBILITY_SERVICE` | Read Uber Driver screen content |
| `INTERNET` | Call Supabase analyze-offer endpoint |
| `FOREGROUND_SERVICE` | Keep overlay alive while Uber Driver is active |

## First-milestone success criteria

Build succeeds if:
1. The overlay bubble appears over Uber Driver
2. The debug log shows raw accessibility text scraped from the Uber Driver screen

If no Uber Eats offer text is exposed by AccessibilityService inside Uber Driver, the app logs the MediaProjection TODO and does not guess.

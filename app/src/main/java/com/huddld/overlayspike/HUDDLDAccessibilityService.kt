package com.huddld.overlayspike

import android.accessibilityservice.AccessibilityService
import android.graphics.Rect
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicLong

class HUDDLDAccessibilityService : AccessibilityService() {

    private val TAG = "HUDDLDAccess"
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val extractionProfile = UberDriverExtractionProfile()
    private val supabaseClient = SupabaseAnalyzeClient()

    // Deduplication: fingerprint -> timestamp
    private val recentFingerprints = HashMap<String, Long>()
    private val DEDUP_WINDOW_MS = 30_000L

    // Counters
    private var cntReads = 0
    private var cntParseSuccess = 0
    private var cntParsePartial = 0
    private var cntParseFailed = 0
    private var cntEndpointSuccess = 0
    private var cntEndpointFailed = 0

    private lateinit var settingsStore: DebugSettingsStore

    override fun onCreate() {
        super.onCreate()
        settingsStore = DebugSettingsStore(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event ?: return
        val pkg = event.packageName?.toString() ?: return

        val debugMode = settingsStore.debugMode
        val isTarget = pkg == "com.ubercab.driver" || (debugMode && pkg.contains("uber"))
        if (!isTarget) return

        val root = rootInActiveWindow ?: return

        cntReads++

        val nodes = mutableListOf<NodeData>()
        collectNodes(root, nodes)
        root.recycle()

        val rawText = nodes.joinToString("\n") { it.text }
        val rawLen = rawText.length

        broadcast("pkg=$pkg | raw_len=$rawLen | reads=$cntReads")
        broadcast("RAW_TEXT:\n${rawText.take(2000)}")

        if (rawText.isBlank()) {
            broadcast("TODO: MediaProjection + ML Kit OCR fallback – AccessibilityService returned no parseable text from $pkg")
            return
        }

        val offer = extractionProfile.parse(rawText)
        val missingStr = offer.missingFields.joinToString(", ").ifEmpty { "none" }

        broadcast("parsed: pay=${offer.pay} dist=${offer.distance} min=${offer.estimatedMinutes} store=${offer.storeName}")
        broadcast("missing=$missingStr conf=${"%.2f".format(offer.confidence)}")

        if (offer.pay == null && offer.distance == null) {
            cntParseFailed++
            broadcast("parse_failed | counters: ${counters()}")
            OverlayBridge.overlayManager?.setWaiting()
            return
        }

        if (offer.pay == null || offer.distance == null) {
            cntParsePartial++
            broadcast("parse_partial | counters: ${counters()}")
            OverlayBridge.overlayManager?.setNeedFields(offer.missingFields)
            return
        }

        cntParseSuccess++
        broadcast("parse_success | counters: ${counters()}")

        val fingerprint = buildFingerprint(offer)
        val now = System.currentTimeMillis()
        val lastSeen = recentFingerprints[fingerprint]
        if (lastSeen != null && now - lastSeen < DEDUP_WINDOW_MS) {
            broadcast("duplicate suppressed (${(now - lastSeen) / 1000}s ago)")
            return
        }
        recentFingerprints[fingerprint] = now
        pruneFingerprints(now)

        scope.launch {
            callEndpoint(offer)
        }
    }

    private suspend fun callEndpoint(offer: ParsedOffer) {
        val token = settingsStore.accessToken
        val apiKey = settingsStore.apiKey
        val mode = settingsStore.mode
        val config = settingsStore.parsedPregameConfig()

        val result = supabaseClient.analyze(offer, config, mode, token, apiKey)

        broadcast("endpoint: status=${result.statusCode} latency=${result.latencyMs}ms")
        broadcast("endpoint_request: ${result.requestBody}")
        broadcast("endpoint_response: ${result.responseBody?.take(1000) ?: "null"}")

        if (result.apiVerdict != null) {
            cntEndpointSuccess++
            broadcast("endpoint_success | verdict=${result.apiVerdict.verdict} | counters: ${counters()}")
            OverlayBridge.overlayManager?.setVerdict(result.apiVerdict)
        } else {
            cntEndpointFailed++
            broadcast("endpoint_failed: ${result.error} | using local fallback | counters: ${counters()}")

            val local = LocalVerdictEngine.evaluate(offer, config, mode)
            broadcast("local_verdict: ${local.verdict} reason=${local.reason}")
            OverlayBridge.overlayManager?.setLocalVerdict(local, offer)
        }
    }

    private fun collectNodes(node: AccessibilityNodeInfo, out: MutableList<NodeData>) {
        val text = node.text?.toString()
            ?: node.contentDescription?.toString()
            ?: ""

        if (text.isNotBlank()) {
            val bounds = Rect()
            node.getBoundsInScreen(bounds)
            out += NodeData(
                text = text,
                className = node.className?.toString() ?: "",
                viewId = node.viewIdResourceName ?: "",
                bounds = bounds.toShortString()
            )
        }

        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            collectNodes(child, out)
            child.recycle()
        }
    }

    private fun buildFingerprint(offer: ParsedOffer): String {
        val prefix = offer.rawText.take(200)
        return "${offer.pay}|${offer.distance}|${offer.estimatedMinutes}|$prefix"
    }

    private fun pruneFingerprints(now: Long) {
        recentFingerprints.entries.removeAll { now - it.value > DEDUP_WINDOW_MS }
    }

    private fun counters() =
        "reads=$cntReads ok=$cntParseSuccess partial=$cntParsePartial fail=$cntParseFailed " +
        "ep_ok=$cntEndpointSuccess ep_fail=$cntEndpointFailed"

    private fun broadcast(msg: String) {
        Log.d(TAG, msg)
        OverlayBridge.logCallback?.invoke(msg)
    }

    override fun onInterrupt() {}

    private data class NodeData(
        val text: String,
        val className: String,
        val viewId: String,
        val bounds: String
    )
}

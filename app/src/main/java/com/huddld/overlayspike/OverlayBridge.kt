package com.huddld.overlayspike

// Singleton bridge between HUDDLDAccessibilityService and OverlayManager / MainActivity.
// Using a simple object is fine for a spike; replace with a bound service or EventBus in prod.
object OverlayBridge {
    var overlayManager: OverlayManager? = null
    var logCallback: ((String) -> Unit)? = null
}

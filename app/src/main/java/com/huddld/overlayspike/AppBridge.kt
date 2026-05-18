package com.huddld.overlayspike

object AppBridge {
    var logCallback: ((String) -> Unit)? = null

    fun log(msg: String) {
        android.util.Log.d("HUDDLD", msg)
        logCallback?.invoke(msg)
    }
}

package com.huddld.overlayspike

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class HUDDLDAccessibilityService : AccessibilityService() {

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val pkg = event?.packageName?.toString() ?: return

        val isTarget = pkg == "com.ubercab.driver" || pkg.contains("uber", ignoreCase = true)
        if (!isTarget) return

        AppBridge.log("pkg=$pkg event=${event.eventType}")

        val root = rootInActiveWindow
        if (root == null) {
            AppBridge.log("pkg=$pkg rootInActiveWindow=null")
            return
        }

        val texts = mutableListOf<String>()
        collectText(root, texts)
        root.recycle()

        if (texts.isEmpty()) {
            AppBridge.log("pkg=$pkg no visible text nodes")
        } else {
            AppBridge.log("pkg=$pkg text_nodes=${texts.size}")
            AppBridge.log("raw:\n${texts.joinToString("\n").take(1000)}")
        }
    }

    private fun collectText(node: AccessibilityNodeInfo, out: MutableList<String>) {
        val t = node.text?.toString()?.trim()
            ?: node.contentDescription?.toString()?.trim()
        if (!t.isNullOrEmpty()) out += t
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            collectText(child, out)
            child.recycle()
        }
    }

    override fun onInterrupt() {}
}

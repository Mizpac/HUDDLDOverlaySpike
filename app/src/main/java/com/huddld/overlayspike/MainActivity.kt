package com.huddld.overlayspike

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var tvLog: TextView
    private lateinit var scrollLog: ScrollView
    private val timeFmt = SimpleDateFormat("HH:mm:ss", Locale.US)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(buildLayout())

        AppBridge.logCallback = { msg ->
            runOnUiThread { appendLog(msg) }
        }

        appendLog("Ready. Overlay permission: ${Settings.canDrawOverlays(this)}")
    }

    override fun onResume() {
        super.onResume()
        appendLog("Overlay permission: ${Settings.canDrawOverlays(this)}")
    }

    private fun buildLayout(): android.widget.LinearLayout {
        val root = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
        }

        fun btn(label: String, action: () -> Unit) = Button(this).apply {
            text = label
            setOnClickListener { action() }
            layoutParams = android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT,
                android.widget.LinearLayout.LayoutParams.WRAP_CONTENT
            ).also { it.bottomMargin = 12 }
        }

        root.addView(btn("Request Overlay Permission") {
            if (!Settings.canDrawOverlays(this)) {
                startActivity(
                    Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName"))
                )
            } else {
                appendLog("Overlay permission already granted")
            }
        })

        root.addView(btn("Open Accessibility Settings") {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        })

        root.addView(btn("Start Overlay") {
            if (!Settings.canDrawOverlays(this)) {
                appendLog("ERROR: grant overlay permission first")
            } else {
                val svcIntent = Intent(this, OverlayService::class.java)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                    startForegroundService(svcIntent)
                else
                    startService(svcIntent)
                appendLog("Overlay service started")
            }
        })

        root.addView(btn("Stop Overlay") {
            stopService(Intent(this, OverlayService::class.java))
            appendLog("Overlay service stopped")
        })

        val logLabel = TextView(this).apply { text = "Log:" }
        root.addView(logLabel)

        tvLog = TextView(this).apply {
            textSize = 11f
            typeface = android.graphics.Typeface.MONOSPACE
            setTextColor(android.graphics.Color.WHITE)
            setTextIsSelectable(true)
        }

        scrollLog = ScrollView(this).apply {
            setBackgroundColor(android.graphics.Color.parseColor("#111111"))
            setPadding(12, 12, 12, 12)
            layoutParams = android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f
            )
            addView(tvLog)
        }
        root.addView(scrollLog)

        return root
    }

    private fun appendLog(msg: String) {
        val line = "${timeFmt.format(Date())} $msg\n"
        tvLog.append(line)
        scrollLog.post { scrollLog.fullScroll(ScrollView.FOCUS_DOWN) }
    }

    override fun onDestroy() {
        AppBridge.logCallback = null
        super.onDestroy()
    }
}

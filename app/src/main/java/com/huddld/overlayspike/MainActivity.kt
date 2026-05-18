package com.huddld.overlayspike

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.text.method.ScrollingMovementMethod
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.huddld.overlayspike.databinding.ActivityMainBinding
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var store: DebugSettingsStore
    private val logLines = ArrayDeque<String>(500)
    private val timeFmt = SimpleDateFormat("HH:mm:ss.SSS", Locale.US)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        store = DebugSettingsStore(this)
        loadSettings()
        setupButtons()
        setupLogBridge()
        updateStatus()
    }

    override fun onResume() {
        super.onResume()
        updateStatus()
    }

    private fun loadSettings() {
        binding.etAccessToken.setText(store.accessToken)
        binding.etApiKey.setText(store.apiKey)
        binding.etMode.setText(store.mode)
        binding.etPregameConfig.setText(store.pregameConfigJson)
        binding.switchDebugMode.isChecked = store.debugMode
    }

    private fun setupButtons() {
        binding.btnSaveSettings.setOnClickListener {
            store.accessToken = binding.etAccessToken.text?.toString()?.trim() ?: ""
            store.apiKey = binding.etApiKey.text?.toString()?.trim() ?: ""
            store.mode = binding.etMode.text?.toString()?.trim() ?: "hustle"
            store.pregameConfigJson = binding.etPregameConfig.text?.toString()?.trim() ?: ""
            store.debugMode = binding.switchDebugMode.isChecked
            Toast.makeText(this, "Settings saved", Toast.LENGTH_SHORT).show()
            appendLog("Settings saved")
        }

        binding.btnRequestOverlay.setOnClickListener {
            if (!Settings.canDrawOverlays(this)) {
                val intent = Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName")
                )
                startActivity(intent)
            } else {
                Toast.makeText(this, "Overlay permission already granted", Toast.LENGTH_SHORT).show()
                appendLog("Overlay permission already granted")
            }
        }

        binding.btnOpenAccessibility.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        binding.btnStartOverlay.setOnClickListener {
            if (!Settings.canDrawOverlays(this)) {
                Toast.makeText(this, "Grant overlay permission first", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            startForegroundService(Intent(this, OverlayService::class.java))
            appendLog("Overlay started")
            updateStatus()
        }

        binding.btnStopOverlay.setOnClickListener {
            stopService(Intent(this, OverlayService::class.java))
            appendLog("Overlay stopped")
            updateStatus()
        }

        binding.btnClearLog.setOnClickListener {
            logLines.clear()
            binding.tvLog.text = ""
        }
    }

    private fun setupLogBridge() {
        OverlayBridge.logCallback = { msg ->
            runOnUiThread { appendLog(msg) }
        }
    }

    private fun appendLog(msg: String) {
        val ts = timeFmt.format(Date())
        val line = "$ts $msg"
        logLines.addFirst(line)
        if (logLines.size > 500) logLines.removeLast()
        binding.tvLog.text = logLines.joinToString("\n")
    }

    private fun updateStatus() {
        val overlayGranted = Settings.canDrawOverlays(this)
        val status = buildString {
            append("Overlay permission: ${if (overlayGranted) "GRANTED" else "DENIED"}")
        }
        binding.tvStatus.text = status
    }

    override fun onDestroy() {
        OverlayBridge.logCallback = null
        super.onDestroy()
    }
}

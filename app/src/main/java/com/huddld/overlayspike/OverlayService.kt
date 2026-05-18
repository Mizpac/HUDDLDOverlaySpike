package com.huddld.overlayspike

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat

class OverlayService : Service() {

    private lateinit var overlayManager: OverlayManager

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        startForeground(NOTIF_ID, buildNotification())

        overlayManager = OverlayManager(this)
        overlayManager.show()
        OverlayBridge.overlayManager = overlayManager
    }

    override fun onDestroy() {
        overlayManager.hide()
        OverlayBridge.overlayManager = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "HUDDLD Overlay",
            NotificationManager.IMPORTANCE_LOW
        ).apply { description = "Keeps the HUDDLD overlay active" }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    private fun buildNotification(): Notification =
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("HUDDLD Overlay active")
            .setContentText("Watching for Uber Driver offers")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setOngoing(true)
            .build()

    companion object {
        private const val CHANNEL_ID = "huddld_overlay"
        private const val NOTIF_ID = 1001
    }
}

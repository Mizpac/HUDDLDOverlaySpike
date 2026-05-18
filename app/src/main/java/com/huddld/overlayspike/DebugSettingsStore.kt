package com.huddld.overlayspike

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import com.google.gson.JsonSyntaxException

class DebugSettingsStore(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences("huddld_debug", Context.MODE_PRIVATE)
    private val gson = Gson()

    var accessToken: String
        get() = prefs.getString("access_token", "") ?: ""
        set(v) = prefs.edit().putString("access_token", v).apply()

    var apiKey: String
        get() = prefs.getString("api_key", "") ?: ""
        set(v) = prefs.edit().putString("api_key", v).apply()

    var mode: String
        get() = prefs.getString("mode", "hustle") ?: "hustle"
        set(v) = prefs.edit().putString("mode", v).apply()

    var pregameConfigJson: String
        get() = prefs.getString("pregame_config", defaultPregameJson()) ?: defaultPregameJson()
        set(v) = prefs.edit().putString("pregame_config", v).apply()

    var debugMode: Boolean
        get() = prefs.getBoolean("debug_mode", false)
        set(v) = prefs.edit().putBoolean("debug_mode", v).apply()

    fun parsedPregameConfig(): PregameConfig = try {
        gson.fromJson(pregameConfigJson, PregameConfig::class.java) ?: PregameConfig()
    } catch (e: JsonSyntaxException) {
        PregameConfig()
    }

    private fun defaultPregameJson() =
        """{"targetPerHr":25,"targetPerMile":1.5,"minPay":6,"mpg":28,"gasPrice":3.45,"state":"TX"}"""
}

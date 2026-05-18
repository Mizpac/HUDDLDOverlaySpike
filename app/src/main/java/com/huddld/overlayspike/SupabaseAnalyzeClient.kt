package com.huddld.overlayspike

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

class SupabaseAnalyzeClient {

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private val json = "application/json; charset=utf-8".toMediaType()

    private val endpoint = "https://dccjedwxcaukxhfuumkq.supabase.co/functions/v1/analyze-offer"

    data class Result(
        val apiVerdict: ApiVerdict?,
        val requestBody: String,
        val responseBody: String?,
        val statusCode: Int,
        val latencyMs: Long,
        val error: String?
    )

    fun analyze(
        offer: ParsedOffer,
        config: PregameConfig,
        mode: String,
        accessToken: String,
        apiKey: String
    ): Result {
        val body = buildRequestBody(offer, config, mode)
        val bodyJson = gson.toJson(body)
        val start = System.currentTimeMillis()

        val request = Request.Builder()
            .url(endpoint)
            .addHeader("Authorization", "Bearer $accessToken")
            .addHeader("apikey", apiKey)
            .addHeader("Content-Type", "application/json")
            .post(bodyJson.toRequestBody(json))
            .build()

        return try {
            val response = client.newCall(request).execute()
            val latency = System.currentTimeMillis() - start
            val responseBody = response.body?.string()
            val statusCode = response.code

            if (response.isSuccessful && responseBody != null) {
                val verdict = parseApiResponse(responseBody)
                Result(verdict, bodyJson, responseBody, statusCode, latency, null)
            } else {
                Result(null, bodyJson, responseBody, statusCode, latency, "HTTP $statusCode")
            }
        } catch (e: IOException) {
            val latency = System.currentTimeMillis() - start
            Result(null, bodyJson, null, -1, latency, e.message)
        }
    }

    private fun buildRequestBody(offer: ParsedOffer, config: PregameConfig, mode: String): JsonObject {
        val obj = JsonObject()
        obj.addProperty("source", "manual")
        offer.pay?.let { obj.addProperty("pay", it) }
        offer.distance?.let { obj.addProperty("distance", it) }
        offer.estimatedMinutes?.let { obj.addProperty("estimatedMinutes", it) } ?: obj.add("estimatedMinutes", com.google.gson.JsonNull.INSTANCE)
        obj.add("itemCount", com.google.gson.JsonNull.INSTANCE)
        obj.addProperty("mode", mode)

        val cfg = JsonObject()
        cfg.addProperty("targetPerHr", config.targetPerHr)
        cfg.addProperty("targetPerMile", config.targetPerMile)
        cfg.addProperty("minPay", config.minPay)
        cfg.addProperty("mpg", config.mpg)
        cfg.addProperty("gasPrice", config.gasPrice)
        cfg.addProperty("state", config.state)
        obj.add("pregameConfig", cfg)

        return obj
    }

    private fun parseApiResponse(responseBody: String): ApiVerdict? = try {
        val root = JsonParser.parseString(responseBody).asJsonObject

        val verdictStr = root.getAsJsonObject("verdict")?.get("verdict")?.asString
        val verdictLabel = when (verdictStr?.lowercase()) {
            "yes" -> VerdictLabel.YES
            "no" -> VerdictLabel.NO
            "your_call" -> VerdictLabel.YOUR_CALL
            else -> null
        } ?: return null

        val computed = root.getAsJsonObject("computed")
        val pocket = computed?.get("pocket")?.asDouble
        val perMile = computed?.get("perMile")?.asDouble
        val perHour = computed?.get("perHour")?.let { if (it.isJsonNull) null else it.asDouble }

        val verdictObj = root.getAsJsonObject("verdict")
        val confidence = verdictObj?.get("confidence")?.asDouble
        val reasons = verdictObj?.getAsJsonArray("reasons")
        val reason = reasons?.firstOrNull()?.asString ?: ""
        val modeFitSummary = verdictObj?.get("modeFitSummary")?.let {
            if (it.isJsonNull) null else it.asString
        }

        ApiVerdict(verdictLabel, pocket, perMile, perHour, reason, confidence, modeFitSummary)
    } catch (e: Exception) {
        null
    }
}

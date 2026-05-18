package com.huddld.overlayspike

data class ParsedOffer(
    val pay: Double?,
    val distance: Double?,
    val estimatedMinutes: Int?,
    val storeName: String?,
    val rawText: String,
    val confidence: Double,
    val missingFields: List<String>
)

data class PregameConfig(
    val targetPerHr: Double = 25.0,
    val targetPerMile: Double = 1.5,
    val minPay: Double = 6.0,
    val mpg: Double = 28.0,
    val gasPrice: Double = 3.45,
    val state: String = "TX"
)

enum class VerdictLabel { YES, NO, YOUR_CALL }

data class LocalVerdict(
    val verdict: VerdictLabel,
    val pocket: Double?,
    val perMile: Double?,
    val perHour: Double?,
    val reason: String
)

data class ApiVerdict(
    val verdict: VerdictLabel,
    val pocket: Double?,
    val perMile: Double?,
    val perHour: Double?,
    val reason: String,
    val confidence: Double?,
    val modeFitSummary: String?
)

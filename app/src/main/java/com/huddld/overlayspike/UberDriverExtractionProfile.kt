package com.huddld.overlayspike

import java.util.regex.Pattern

class UberDriverExtractionProfile : ExtractionProfile {

    override fun canHandle(packageName: String, rawText: String): Boolean =
        packageName.contains("ubercab.driver") || packageName.contains("uber")

    override fun parse(rawText: String): ParsedOffer {
        val pay = parsePay(rawText)
        val distance = parseDistance(rawText)
        val minutes = parseMinutes(rawText)
        val storeName = parseStoreName(rawText)

        val missing = mutableListOf<String>()
        if (pay == null) missing += "pay"
        if (distance == null) missing += "distance"
        if (minutes == null) missing += "estimatedMinutes"

        val points = listOf(pay, distance, minutes?.toDouble()).count { it != null }
        val confidence = points / 3.0

        return ParsedOffer(
            pay = pay,
            distance = distance,
            estimatedMinutes = minutes,
            storeName = storeName,
            rawText = rawText,
            confidence = confidence,
            missingFields = missing
        )
    }

    private fun parsePay(text: String): Double? {
        // Match "$9.75" or standalone "9.75" near currency context
        val dollarPattern = Pattern.compile("""\$\s*(\d+(?:\.\d+)?)""")
        val m = dollarPattern.matcher(text)
        if (m.find()) return m.group(1)?.toDoubleOrNull()

        // Fallback: bare number that looks like a dollar amount
        val barePattern = Pattern.compile("""(?:^|[\s(])(\d{1,3}\.\d{2})(?:$|[\s)])""")
        val m2 = barePattern.matcher(text)
        if (m2.find()) return m2.group(1)?.toDoubleOrNull()

        return null
    }

    private fun parseDistance(text: String): Double? {
        // "3.4 mi" or "3.4 miles"
        val pattern = Pattern.compile("""(\d+(?:\.\d+)?)\s*mi(?:les?)?""", Pattern.CASE_INSENSITIVE)
        val m = pattern.matcher(text)
        return if (m.find()) m.group(1)?.toDoubleOrNull() else null
    }

    private fun parseMinutes(text: String): Int? {
        // "16 min", "16 mins", "Estimated time 16 min", "3.4 mi · 16 min"
        val pattern = Pattern.compile("""(\d+)\s*min(?:s|utes?)?""", Pattern.CASE_INSENSITIVE)
        val m = pattern.matcher(text)
        return if (m.find()) m.group(1)?.toIntOrNull() else null
    }

    private fun parseStoreName(text: String): String? {
        // Heuristic: lines that look like a restaurant/store name (title-cased, short, no digits)
        val lines = text.lines()
        for (line in lines) {
            val trimmed = line.trim()
            if (trimmed.length in 3..50
                && trimmed.none { it.isDigit() }
                && trimmed.none { it == '$' }
                && !trimmed.contains("min", ignoreCase = true)
                && !trimmed.contains("mi", ignoreCase = true)
                && trimmed.first().isUpperCase()
            ) {
                return trimmed
            }
        }
        return null
    }
}

package com.huddld.overlayspike

interface ExtractionProfile {
    fun canHandle(packageName: String, rawText: String): Boolean
    fun parse(rawText: String): ParsedOffer
}

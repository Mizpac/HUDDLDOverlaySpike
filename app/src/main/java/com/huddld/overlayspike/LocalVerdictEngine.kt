package com.huddld.overlayspike

object LocalVerdictEngine {

    fun evaluate(offer: ParsedOffer, config: PregameConfig, mode: String): LocalVerdict {
        val pay = offer.pay ?: return LocalVerdict(
            VerdictLabel.YOUR_CALL, null, null, null, "Missing pay"
        )
        val distance = offer.distance ?: return LocalVerdict(
            VerdictLabel.YOUR_CALL, null, null, null, "Missing distance"
        )

        val gasCost = (distance / config.mpg) * config.gasPrice
        val pocket = pay - gasCost
        val perMile = pay / distance
        val perHour = offer.estimatedMinutes?.let { pay / (it / 60.0) }

        if (mode == "audible") {
            return LocalVerdict(VerdictLabel.YOUR_CALL, pocket, perMile, perHour, "Audible mode")
        }

        var fails = 0
        val reasons = mutableListOf<String>()

        if (pay < config.minPay) { fails++; reasons += "pay $${"%.2f".format(pay)} < min $${"%.2f".format(config.minPay)}" }
        if (perMile < config.targetPerMile) { fails++; reasons += "$${"%.2f".format(perMile)}/mi < target $${"%.2f".format(config.targetPerMile)}" }
        if (perHour != null && perHour < config.targetPerHr) { fails++; reasons += "$${"%.0f".format(perHour)}/hr < target $${"%.0f".format(config.targetPerHr)}" }

        val verdict = when {
            fails >= 2 -> VerdictLabel.NO
            fails == 1 -> VerdictLabel.YOUR_CALL
            else -> VerdictLabel.YES
        }
        val reason = if (reasons.isEmpty()) "Meets all targets" else reasons.first()

        return LocalVerdict(verdict, pocket, perMile, perHour, reason)
    }
}

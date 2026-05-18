package com.huddld.overlayspike

import android.content.Context
import android.graphics.PixelFormat
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import androidx.core.content.ContextCompat
import com.huddld.overlayspike.databinding.OverlayBubbleBinding

class OverlayManager(private val context: Context) {

    private val windowManager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var binding: OverlayBubbleBinding? = null
    private var params: WindowManager.LayoutParams? = null
    private var isShowing = false

    fun show() {
        if (isShowing) return

        val inflater = LayoutInflater.from(context)
        binding = OverlayBubbleBinding.inflate(inflater)

        params = WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                    WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = 16
            y = 200
        }

        setupDrag()
        setupExpandCollapse()

        windowManager.addView(binding!!.root, params)
        isShowing = true
        setWaiting()
    }

    fun hide() {
        if (!isShowing) return
        binding?.let { windowManager.removeView(it.root) }
        binding = null
        isShowing = false
    }

    fun setWaiting() = updateState("waiting", null, null)

    fun setNeedFields(missing: List<String>) {
        val msg = "Need ${missing.joinToString(", ")}"
        updateState(msg, null, null)
    }

    fun setVerdict(verdict: ApiVerdict) {
        val label = when (verdict.verdict) {
            VerdictLabel.YES -> "YES"
            VerdictLabel.NO -> "NO"
            VerdictLabel.YOUR_CALL -> "YOUR CALL"
        }
        val color = when (verdict.verdict) {
            VerdictLabel.YES -> R.color.verdict_yes
            VerdictLabel.NO -> R.color.verdict_no
            VerdictLabel.YOUR_CALL -> R.color.verdict_your_call
        }
        updateState(label, color, verdict)
    }

    fun setLocalVerdict(verdict: LocalVerdict, offer: ParsedOffer) {
        val label = when (verdict.verdict) {
            VerdictLabel.YES -> "YES"
            VerdictLabel.NO -> "NO"
            VerdictLabel.YOUR_CALL -> "YOUR CALL"
        }
        val color = when (verdict.verdict) {
            VerdictLabel.YES -> R.color.verdict_yes
            VerdictLabel.NO -> R.color.verdict_no
            VerdictLabel.YOUR_CALL -> R.color.verdict_your_call
        }
        val b = binding ?: return
        b.tvState.text = label
        b.tvState.setTextColor(ContextCompat.getColor(context, color))
        b.tvVerdict.text = label
        b.tvVerdict.setTextColor(ContextCompat.getColor(context, color))
        b.tvPocket.text = verdict.pocket?.let { "Pocket: $${"%.2f".format(it)}" } ?: ""
        b.tvPerMile.text = verdict.perMile?.let { "$/mi: ${"%.2f".format(it)}" } ?: ""
        b.tvPerHour.text = verdict.perHour?.let { "$/hr: ${"%.0f".format(it)}" } ?: ""
        b.tvReason.text = verdict.reason
        b.tvConfidence.text = "conf: ${"%.0f".format(offer.confidence * 100)}% (local fallback)"
        b.tvParsedOffer.text = "pay=${offer.pay} dist=${offer.distance} min=${offer.estimatedMinutes}"
    }

    fun setError(msg: String) = updateState("error", null, null)

    private fun updateState(state: String, colorRes: Int?, verdict: ApiVerdict?) {
        val b = binding ?: return
        b.tvState.text = state
        val color = colorRes ?: R.color.verdict_waiting
        b.tvState.setTextColor(ContextCompat.getColor(context, color))

        if (verdict != null) {
            val label = when (verdict.verdict) {
                VerdictLabel.YES -> "YES"
                VerdictLabel.NO -> "NO"
                VerdictLabel.YOUR_CALL -> "YOUR CALL"
            }
            b.tvVerdict.text = label
            b.tvVerdict.setTextColor(ContextCompat.getColor(context, color))
            b.tvPocket.text = verdict.pocket?.let { "Pocket: $${"%.2f".format(it)}" } ?: ""
            b.tvPerMile.text = verdict.perMile?.let { "$/mi: ${"%.2f".format(it)}" } ?: ""
            b.tvPerHour.text = verdict.perHour?.let { "$/hr: ${"%.0f".format(it)}" } ?: ""
            b.tvReason.text = verdict.reason
            b.tvConfidence.text = "conf: ${verdict.confidence?.let { "${"%.0f".format(it * 100)}%" } ?: "?"}"
            b.tvParsedOffer.text = ""
        }
    }

    private fun setupExpandCollapse() {
        val b = binding ?: return
        b.collapsedRow.setOnClickListener {
            if (b.expandedPanel.visibility == View.GONE) {
                b.expandedPanel.visibility = View.VISIBLE
            }
        }
        b.btnHide.setOnClickListener {
            b.expandedPanel.visibility = View.GONE
        }
    }

    private fun setupDrag() {
        val b = binding ?: return
        var startX = 0f; var startY = 0f
        var startParamX = 0; var startParamY = 0

        b.root.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    startX = event.rawX; startY = event.rawY
                    startParamX = params!!.x; startParamY = params!!.y
                    false
                }
                MotionEvent.ACTION_MOVE -> {
                    params!!.x = startParamX + (event.rawX - startX).toInt()
                    params!!.y = startParamY + (event.rawY - startY).toInt()
                    windowManager.updateViewLayout(b.root, params)
                    true
                }
                else -> false
            }
        }
    }
}

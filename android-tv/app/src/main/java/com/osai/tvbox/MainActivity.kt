package com.osai.tvbox

import android.app.Activity
import android.app.AlertDialog
import android.content.SharedPreferences
import android.os.Bundle
import android.view.KeyEvent
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.Toast

class MainActivity : Activity() {

    private lateinit var web: WebView
    private lateinit var prefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = getSharedPreferences("osai", MODE_PRIVATE)

        web = WebView(this)
        setContentView(web)

        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
            loadWithOverviewMode = true
            useWideViewPort = true
        }
        web.setBackgroundColor(0xFF05070F.toInt())
        web.webViewClient = WebViewClient()
        web.webChromeClient = WebChromeClient()

        val url = prefs.getString(KEY_SERVER, null)
        if (url.isNullOrBlank()) askServerUrl(firstRun = true) else load(url)
    }

    private fun load(serverUrl: String) {
        val base = serverUrl.trim().trimEnd('/')
        prefs.edit().putString(KEY_SERVER, base).apply()
        web.loadUrl("$base/tv")
    }

    private fun askServerUrl(firstRun: Boolean) {
        val input = EditText(this).apply {
            hint = "http://192.168.1.105:8000"
            setText(prefs.getString(KEY_SERVER, "http://192.168.1.105:8000"))
            setSingleLine(true)
        }
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.server_title))
            .setMessage(getString(R.string.server_message))
            .setView(input)
            .setCancelable(false)
            .setPositiveButton(getString(R.string.save)) { _, _ -> load(input.text.toString()) }
            .setNegativeButton(if (firstRun) getString(R.string.exit) else getString(R.string.cancel)) { _, _ ->
                if (firstRun) finish()
            }
            .show()
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_MENU) {
            askServerUrl(firstRun = false)
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onBackPressed() {
        val base = prefs.getString(KEY_SERVER, "")?.trimEnd('/') ?: ""
        if (web.canGoBack() && web.url != "$base/tv") {
            web.goBack()
        } else {
            if (DOUBLE_EXIT && lastExit + 2000 > System.currentTimeMillis()) {
                finish()
            } else {
                lastExit = System.currentTimeMillis()
                Toast.makeText(this, R.string.press_back_again, Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onPause() {
        super.onPause()
        web.onPause()
    }

    override fun onResume() {
        super.onResume()
        web.onResume()
    }

    companion object {
        private const val KEY_SERVER = "server_url"
        private const val DOUBLE_EXIT = true
        private var lastExit = 0L
    }
}

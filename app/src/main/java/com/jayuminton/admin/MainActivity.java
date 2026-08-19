package com.jayuminton.admin;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.media.AudioManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebStorage;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;

public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final String ADMIN_URL =
            "https://jayuminton-push--admin-cloudflare-vnext-z3bgvi2g.web.app/?app=admin&native=1";
    private static final String MEMBER_PWA_URL = "https://jayuminton-push.web.app/";
    private static final String APK_WEB_BUILD = "1997-cloudflare-admin-vnext";
    private static final String PREFS = "jayuminton_audio_state";
    private static final String KEY_WAS_DUCKING = "was_ducking";
    private static final String KEY_MEDIA_VOLUME = "media_volume";
    private static final String KEY_ALARM_VOLUME = "alarm_volume";
    private static final int VOICE_VOLUME_STEP = 6;

    private WebView webView;
    private TextToSpeech tts;
    private AudioManager audioManager;
    private final AtomicBoolean ttsReady = new AtomicBoolean(false);
    private final AtomicBoolean speaking = new AtomicBoolean(false);
    private final Object audioLock = new Object();
    private boolean ducking;
    private int originalMediaVolume = -1;
    private int originalAlarmVolume = -1;
    private SpeakRequest pendingRequest;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.WHITE);
        getWindow().setNavigationBarColor(Color.WHITE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            int flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            }
            getWindow().getDecorView().setSystemUiVisibility(flags);
        }

        setContentView(R.layout.activity_main);
        audioManager = (AudioManager) getSystemService(AUDIO_SERVICE);
        recoverAudioIfNeeded();
        tts = new TextToSpeech(this, this);
        configureWebView();
    }

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    private void configureWebView() {
        webView = findViewById(R.id.webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setTextZoom(100);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setUserAgentString(settings.getUserAgentString() + " JayumintonNative/199.7 CloudflareAdmin/1997");

        webView.clearCache(true);
        webView.clearHistory();
        WebStorage.getInstance().deleteAllData();

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);
        cookieManager.removeSessionCookies(null);
        cookieManager.flush();

        webView.addJavascriptInterface(new VoiceBridge(), "NativeVoice");
        webView.addJavascriptInterface(new BrowserBridge(), "NativeBrowser");
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (isMemberPwaUri(uri)) {
                    openMemberPwaInBrowser(uri.toString());
                    return true;
                }
                String scheme = uri.getScheme();
                if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                    return false;
                }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                view.evaluateJavascript(
                        "window.__JAYUMINTON_NATIVE_APP__=true;" +
                        "window.__JAYUMINTON_APK_WEB_BUILD__='" + APK_WEB_BUILD + "';" +
                        "document.documentElement.setAttribute('data-native-app','1');" +
                        "document.documentElement.setAttribute('data-apk-web-build','" + APK_WEB_BUILD + "');",
                        null
                );
            }
        });

        String freshAdminUrl = ADMIN_URL
                + "&apkBuild=" + APK_WEB_BUILD
                + "&ts=" + System.currentTimeMillis();
        Map<String, String> headers = new HashMap<>();
        headers.put("Cache-Control", "no-cache, no-store, must-revalidate");
        headers.put("Pragma", "no-cache");
        headers.put("Expires", "0");
        webView.loadUrl(freshAdminUrl, headers);
    }

    private boolean isMemberPwaUri(Uri uri) {
        return uri != null && "jayuminton-push.web.app".equalsIgnoreCase(uri.getHost());
    }

    private boolean tryOpenBrowserPackage(String packageName, String url) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            intent.setPackage(packageName);
            startActivity(intent);
            return true;
        } catch (ActivityNotFoundException error) {
            return false;
        }
    }

    private void openMemberPwaInBrowser(String requestedUrl) {
        String url = requestedUrl == null || requestedUrl.trim().isEmpty()
                ? MEMBER_PWA_URL
                : requestedUrl;
        if (tryOpenBrowserPackage("com.android.chrome", url)) return;
        if (tryOpenBrowserPackage("com.sec.android.app.sbrowser", url)) return;
        Toast.makeText(
                this,
                "PWA 설치는 Chrome 또는 삼성 인터넷에서 진행해 주세요.",
                Toast.LENGTH_LONG
        ).show();
    }

    @Override
    public void onInit(int status) {
        if (status != TextToSpeech.SUCCESS) {
            ttsReady.set(false);
            return;
        }

        int languageResult = tts.setLanguage(Locale.KOREA);
        ttsReady.set(languageResult != TextToSpeech.LANG_MISSING_DATA &&
                languageResult != TextToSpeech.LANG_NOT_SUPPORTED);
        selectBestKoreanFemaleVoice();
        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override
            public void onStart(String utteranceId) {
                speaking.set(true);
            }

            @Override
            public void onDone(String utteranceId) {
                speaking.set(false);
                runOnUiThread(MainActivity.this::restoreAudio);
            }

            @Override
            public void onError(String utteranceId) {
                speaking.set(false);
                runOnUiThread(MainActivity.this::restoreAudio);
            }

            @Override
            public void onStop(String utteranceId, boolean interrupted) {
                speaking.set(false);
                runOnUiThread(MainActivity.this::restoreAudio);
            }
        });

        SpeakRequest request = pendingRequest;
        pendingRequest = null;
        if (request != null && ttsReady.get()) {
            runOnUiThread(() -> speakNative(request));
        }
    }

    private void selectBestKoreanFemaleVoice() {
        if (tts == null || Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) return;
        Set<Voice> available = tts.getVoices();
        if (available == null || available.isEmpty()) return;

        List<Voice> koreanVoices = new ArrayList<>();
        for (Voice voice : available) {
            Locale locale = voice.getLocale();
            if (locale != null && "ko".equalsIgnoreCase(locale.getLanguage())) {
                koreanVoices.add(voice);
            }
        }
        if (koreanVoices.isEmpty()) return;

        koreanVoices.sort((left, right) -> {
            int scoreCompare = Integer.compare(femaleVoiceScore(right), femaleVoiceScore(left));
            if (scoreCompare != 0) return scoreCompare;
            int networkCompare = Boolean.compare(left.isNetworkConnectionRequired(), right.isNetworkConnectionRequired());
            if (networkCompare != 0) return networkCompare;
            return Integer.compare(right.getQuality(), left.getQuality());
        });
        tts.setVoice(koreanVoices.get(0));
    }

    private int femaleVoiceScore(Voice voice) {
        String name = voice.getName() == null ? "" : voice.getName().toLowerCase(Locale.ROOT);
        int score = 0;
        String[] preferred = {"female", "woman", "여성", "suna", "seoyeon", "yuna", "ism", "kod"};
        for (String token : preferred) {
            if (name.contains(token)) score += 20;
        }
        if (!voice.isNetworkConnectionRequired()) score += 8;
        score += Math.max(0, voice.getQuality());
        return score;
    }

    private void speakNative(SpeakRequest request) {
        if (tts == null || !ttsReady.get()) {
            pendingRequest = request;
            return;
        }

        beginStrongDucking();
        speaking.set(true);
        tts.stop();
        tts.setSpeechRate(clamp(request.rate, 0.75f, 1.15f));
        tts.setPitch(clamp(request.pitch, 0.90f, 1.15f));
        selectBestKoreanFemaleVoice();

        Bundle params = new Bundle();
        params.putInt(TextToSpeech.Engine.KEY_PARAM_STREAM, AudioManager.STREAM_ALARM);
        params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, 1.0f);
        int result = tts.speak(request.text, TextToSpeech.QUEUE_FLUSH, params, request.id);
        if (result == TextToSpeech.ERROR) {
            speaking.set(false);
            restoreAudio();
        }
    }

    private float clamp(float value, float min, float max) {
        if (Float.isNaN(value) || Float.isInfinite(value)) return 1.0f;
        return Math.max(min, Math.min(max, value));
    }

    private void beginStrongDucking() {
        synchronized (audioLock) {
            if (ducking || audioManager == null) return;
            originalMediaVolume = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC);
            originalAlarmVolume = audioManager.getStreamVolume(AudioManager.STREAM_ALARM);

            getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                    .putBoolean(KEY_WAS_DUCKING, true)
                    .putInt(KEY_MEDIA_VOLUME, originalMediaVolume)
                    .putInt(KEY_ALARM_VOLUME, originalAlarmVolume)
                    .apply();

            try {
                int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
                int minimumMusic = maxMedia > 0 ? 1 : 0;
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, minimumMusic, 0);

                int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);
                int voiceStep = Math.max(1, Math.min(VOICE_VOLUME_STEP, maxAlarm));
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, voiceStep, 0);
                ducking = true;
            } catch (SecurityException error) {
                ducking = false;
                getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
            }
        }
    }

    private void restoreAudio() {
        synchronized (audioLock) {
            if (audioManager == null) return;
            try {
                if (originalMediaVolume >= 0) {
                    audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, originalMediaVolume, 0);
                }
                if (originalAlarmVolume >= 0) {
                    audioManager.setStreamVolume(AudioManager.STREAM_ALARM, originalAlarmVolume, 0);
                }
            } catch (SecurityException ignored) {
            }
            ducking = false;
            originalMediaVolume = -1;
            originalAlarmVolume = -1;
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
        }
    }

    private void recoverAudioIfNeeded() {
        boolean wasDucking = getSharedPreferences(PREFS, MODE_PRIVATE)
                .getBoolean(KEY_WAS_DUCKING, false);
        if (!wasDucking || audioManager == null) return;
        int media = getSharedPreferences(PREFS, MODE_PRIVATE).getInt(KEY_MEDIA_VOLUME, -1);
        int alarm = getSharedPreferences(PREFS, MODE_PRIVATE).getInt(KEY_ALARM_VOLUME, -1);
        try {
            if (media >= 0) audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, media, 0);
            if (alarm >= 0) audioManager.setStreamVolume(AudioManager.STREAM_ALARM, alarm, 0);
        } catch (SecurityException ignored) {
        }
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onStop() {
        super.onStop();
        if (!speaking.get()) restoreAudio();
    }

    @Override
    protected void onDestroy() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        restoreAudio();
        if (webView != null) {
            webView.removeJavascriptInterface("NativeVoice");
            webView.removeJavascriptInterface("NativeBrowser");
            webView.destroy();
        }
        super.onDestroy();
    }

    private static final class SpeakRequest {
        final String id;
        final String text;
        final float rate;
        final float pitch;
        final String requestedVoiceName;

        SpeakRequest(String id, String text, float rate, float pitch, String requestedVoiceName) {
            this.id = id == null || id.trim().isEmpty() ? "jayuminton_tts" : id;
            this.text = text == null ? "" : text;
            this.rate = rate;
            this.pitch = pitch;
            this.requestedVoiceName = requestedVoiceName == null ? "" : requestedVoiceName;
        }
    }

    public final class VoiceBridge {
        @JavascriptInterface
        public void speak(String id, String text, double rate, double pitch, String requestedVoiceName) {
            SpeakRequest request = new SpeakRequest(
                    id,
                    text,
                    (float) rate,
                    (float) pitch,
                    requestedVoiceName
            );
            runOnUiThread(() -> speakNative(request));
        }

        @JavascriptInterface
        public void stop() {
            runOnUiThread(() -> {
                if (tts != null) tts.stop();
                speaking.set(false);
                restoreAudio();
            });
        }

        @JavascriptInterface
        public boolean isSpeaking() {
            return speaking.get() || (tts != null && tts.isSpeaking());
        }
    }

    public final class BrowserBridge {
        @JavascriptInterface
        public void openPwa() {
            runOnUiThread(() -> openMemberPwaInBrowser(MEMBER_PWA_URL));
        }

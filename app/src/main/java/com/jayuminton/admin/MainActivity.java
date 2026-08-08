package com.jayuminton.admin;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.media.AudioManager;
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

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;

public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final String ADMIN_URL =
            "https://script.google.com/macros/s/AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q/exec?mode=admin";
    private static final String APK_WEB_BUILD = "1994-fresh-admin";
    private static final String PREFS = "jayuminton_audio_state";
    private static final String KEY_WAS_DUCKING = "was_ducking";
    private static final String KEY_MEDIA_VOLUME = "media_volume";
    private static final String KEY_ALARM_VOLUME = "alarm_volume";

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
        settings.setUserAgentString(settings.getUserAgentString() + " JayumintonNative/1.4 FreshAdmin/1994");

        /*
         * 관리자 APK는 웹 화면을 껍데기처럼 띄우는 WebView 앱이다.
         * 예전 버전은 DOM storage/localStorage와 WebView cache를 계속 보존해서
         * jayuminton_admin_session_v1 로그인 세션과 오래된 HTML/JS가 남을 수 있었다.
         * 앱을 새로 시작할 때 APK WebView 저장소와 캐시를 초기화해서
         * 항상 최신 배포본을 새 로그인부터 읽게 한다.
         */
        webView.clearCache(true);
        webView.clearHistory();
        WebStorage.getInstance().deleteAllData();

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);
        cookieManager.removeSessionCookies(null);
        cookieManager.flush();

        webView.addJavascriptInterface(new VoiceBridge(), "NativeVoice");
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
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

            int maxMedia = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC);
            int minimumMusic = maxMedia > 0 ? 1 : 0;
            audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, minimumMusic, 0);

            int maxAlarm = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM);
            int clearVoiceAlarm = Math.max(1, Math.round(maxAlarm * 0.85f));
            if (originalAlarmVolume < clearVoiceAlarm) {
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, clearVoiceAlarm, 0);
            }
            ducking = true;
        }
    }

    private void restoreAudio() {
        synchronized (audioLock) {
            if (audioManager == null) return;
            if (originalMediaVolume >= 0) {
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, originalMediaVolume, 0);
            }
            if (originalAlarmVolume >= 0) {
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, originalAlarmVolume, 0);
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
        if (media >= 0) audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, media, 0);
        if (alarm >= 0) audioManager.setStreamVolume(AudioManager.STREAM_ALARM, alarm, 0);
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
}

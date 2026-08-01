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
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;

public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final String ADMIN_URL =
            "https://script.google.com/macros/s/AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q/exec?mode=admin";
    private static final String PREFS = "jayuminton_audio_state";
    private static final String KEY_WAS_DUCKING = "was_ducking";
    private static final String KEY_MEDIA_VOLUME = "media_volume";
    private static final String KEY_ALARM_VOLUME = "alarm_volume";

    private static final String PUSH_HOOK_SCRIPT = """
            (function installJayumintonAssignmentPushHook(){
              if (window.__jayumintonAssignmentPushHookInstalled) return;
              var attempts = 0;

              function normalizeMembers(members){
                return Array.isArray(members)
                  ? members.filter(function(member){
                      return member && member.id != null &&
                        String(member.name || '').trim();
                    }).map(function(member){
                      return {
                        id: String(member.id),
                        name: String(member.name || '').trim()
                      };
                    })
                  : [];
              }

              function membersFromIds(ids){
                if (!Array.isArray(ids)) return [];
                return normalizeMembers(ids.map(function(id){
                  try {
                    if (typeof memberById === 'function') {
                      return memberById(id);
                    }
                    return Array.isArray(STATE.members)
                      ? STATE.members.find(function(member){
                          return member && String(member.id) === String(id);
                        })
                      : null;
                  } catch (error) {
                    return null;
                  }
                }));
              }

              function mostElapsedCourtNo(){
                try {
                  var fullCourts = [1,2,3,4].filter(function(courtNo){
                    return STATE && STATE.courts &&
                      Array.isArray(STATE.courts[courtNo]) &&
                      STATE.courts[courtNo].length === 4;
                  });
                  if (!fullCourts.length) return 0;

                  var timed = fullCourts.map(function(courtNo){
                    var raw = STATE.courtStartedAt &&
                      (STATE.courtStartedAt[courtNo] ||
                       STATE.courtStartedAt[String(courtNo)] || '');
                    var startedAt = Date.parse(String(raw || ''));
                    return {
                      courtNo: courtNo,
                      startedAt: Number.isFinite(startedAt)
                        ? startedAt
                        : Number.POSITIVE_INFINITY
                    };
                  }).sort(function(left, right){
                    return left.startedAt - right.startedAt ||
                      left.courtNo - right.courtNo;
                  });

                  if (Number.isFinite(timed[0].startedAt)) {
                    return timed[0].courtNo;
                  }
                  return fullCourts.sort(function(a,b){ return a-b; })[0];
                } catch (error) {
                  return 0;
                }
              }

              function makeEventId(prefix, courtNo, members){
                var ids = members.map(function(member){
                  return member.id;
                }).sort();
                return prefix + '_' + Date.now().toString(36) + '_' +
                  String(courtNo || 0) + '_' + ids.join('_');
              }

              function publish(payload){
                try {
                  window.NativePush.publishAssignment(
                    JSON.stringify(payload)
                  );
                } catch (error) {}
              }

              function installHook(){
                if (window.__jayumintonAssignmentPushHookInstalled) return true;
                if (!window.NativePush) return false;
                if (typeof rememberVoiceAnnouncement !== 'function') return false;

                var originalRememberVoiceAnnouncement = rememberVoiceAnnouncement;
                rememberVoiceAnnouncement = function(courtNo, members){
                  var result = originalRememberVoiceAnnouncement.apply(this, arguments);
                  try {
                    var assigned = normalizeMembers(members);
                    if (assigned.length === 4) {
                      publish({
                        type: 'court_assignment',
                        assignmentId: makeEventId(
                          'court', Number(courtNo), assigned
                        ),
                        courtNo: Number(courtNo),
                        members: assigned
                      });

                      var promoted = membersFromIds(
                        STATE && Array.isArray(STATE.waitGroups)
                          ? (STATE.waitGroups[0] || [])
                          : []
                      );
                      if (promoted.length > 0 && promoted.length <= 4) {
                        var expectedCourtNo = mostElapsedCourtNo();
                        if (expectedCourtNo >= 1 && expectedCourtNo <= 4) {
                          publish({
                            type: 'wait1_ready',
                            assignmentId: makeEventId(
                              'wait1', expectedCourtNo, promoted
                            ),
                            expectedCourtNo: expectedCourtNo,
                            members: promoted
                          });
                        }
                      }
                    }
                  } catch (error) {}
                  return result;
                };
                window.__jayumintonAssignmentPushHookInstalled = true;
                return true;
              }

              if (installHook()) return;
              var timer = setInterval(function(){
                attempts += 1;
                if (installHook() || attempts >= 300) clearInterval(timer);
              }, 100);
            })();
            """;

    private WebView webView;
    private TextToSpeech tts;
    private AudioManager audioManager;
    private final AtomicBoolean ttsReady = new AtomicBoolean(false);
    private final AtomicBoolean speaking = new AtomicBoolean(false);
    private final Object audioLock = new Object();
    private final ExecutorService pushExecutor = Executors.newSingleThreadExecutor();
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
        findViewById(R.id.refreshButton).setOnClickListener(view -> refreshPage());
    }

    private void refreshPage() {
        if (tts != null) tts.stop();
        speaking.set(false);
        restoreAudio();
        if (webView != null) webView.reload();
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
        settings.setUserAgentString(settings.getUserAgentString() + " JayumintonNative/1.5");

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);

        webView.addJavascriptInterface(new VoiceBridge(), "NativeVoice");
        webView.addJavascriptInterface(new PushBridge(), "NativePush");
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
                                "document.documentElement.setAttribute('data-native-app','1');",
                        null
                );
                view.evaluateJavascript(PUSH_HOOK_SCRIPT, null);
            }
        });
        webView.loadUrl(ADMIN_URL);
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
            int minimumMusic = maxMedia > 0 ? Math.min(6, maxMedia) : 0;
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

    private void publishAssignment(String payloadJson) {
        if (BuildConfig.PUSH_FUNCTION_URL.trim().isEmpty() ||
                BuildConfig.PUSH_SHARED_SECRET.trim().isEmpty()) {
            return;
        }

        pushExecutor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                JSONObject payload = new JSONObject(payloadJson == null ? "{}" : payloadJson);
                String type = payload.optString("type", "court_assignment").trim();
                String assignmentId = payload.optString("assignmentId", "").trim();
                JSONArray members = payload.optJSONArray("members");
                int memberCount = members == null ? 0 : members.length();

                boolean validCourtAssignment =
                        "court_assignment".equals(type) &&
                                payload.optInt("courtNo", 0) >= 1 &&
                                payload.optInt("courtNo", 0) <= 4 &&
                                memberCount == 4;
                boolean validWaitOneReady =
                        "wait1_ready".equals(type) &&
                                payload.optInt("expectedCourtNo", 0) >= 1 &&
                                payload.optInt("expectedCourtNo", 0) <= 4 &&
                                memberCount >= 1 && memberCount <= 4;

                if (assignmentId.isEmpty() ||
                        (!validCourtAssignment && !validWaitOneReady)) {
                    return;
                }

                URL url = new URL(BuildConfig.PUSH_FUNCTION_URL);
                connection = (HttpURLConnection) url.openConnection();
                connection.setConnectTimeout(8000);
                connection.setReadTimeout(12000);
                connection.setRequestMethod("POST");
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                connection.setRequestProperty("X-Jayuminton-Key", BuildConfig.PUSH_SHARED_SECRET);

                byte[] body = payload.toString().getBytes(StandardCharsets.UTF_8);
                connection.setFixedLengthStreamingMode(body.length);
                try (OutputStream output = connection.getOutputStream()) {
                    output.write(body);
                }

                int status = connection.getResponseCode();
                InputStream response = status >= 200 && status < 300
                        ? connection.getInputStream()
                        : connection.getErrorStream();
                if (response != null) {
                    try (InputStream input = response) {
                        byte[] buffer = new byte[512];
                        while (input.read(buffer) != -1) {
                            // Drain the response so the HTTP connection can close cleanly.
                        }
                    }
                }
            } catch (Exception ignored) {
                // Notification failure must never interrupt court operation or TTS.
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
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
        pushExecutor.shutdownNow();
        if (webView != null) {
            webView.removeJavascriptInterface("NativeVoice");
            webView.removeJavascriptInterface("NativePush");
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

    public final class PushBridge {
        @JavascriptInterface
        public void publishAssignment(String payloadJson) {
            MainActivity.this.publishAssignment(payloadJson);
        }
    }
}

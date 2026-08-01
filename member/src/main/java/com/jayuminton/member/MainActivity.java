package com.jayuminton.member;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import com.google.firebase.messaging.FirebaseMessaging;

import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.text.Collator;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final String MEMBER_URL =
            "https://script.google.com/macros/s/AKfycbwVgdQG-DXbgxCgd8L11WA57-DCVaOwF4Sc_lktAZZ0yPJSCIosOOKkmKe3oU8a5pfJ7Q/exec";
    private static final int REQUEST_NOTIFICATIONS = 1501;

    private static final String READ_MEMBER_LIST_SCRIPT = """
            (function(){
              try {
                if (typeof STATE === 'undefined' || !Array.isArray(STATE.members)) {
                  return JSON.stringify([]);
                }
                return JSON.stringify(
                  STATE.members.map(function(member){
                    return {
                      id: String(member && member.id || ''),
                      name: String(member && member.name || '').trim()
                    };
                  }).filter(function(member){
                    return member.id && member.name;
                  })
                );
              } catch (error) {
                return JSON.stringify([]);
              }
            })();
            """;

    private WebView webView;
    private TextView selectedMemberText;
    private Button selectMemberButton;

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
        selectedMemberText = findViewById(R.id.selectedMemberText);
        selectMemberButton = findViewById(R.id.selectMemberButton);
        selectMemberButton.setOnClickListener(view -> loadMembersAndShowPicker());

        JayumintonMessagingService.ensureNotificationChannel(this);
        requestNotificationPermission();
        configureWebView();
        restoreSubscription();
        updateSelectedMemberText();
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {
        webView = findViewById(R.id.webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setTextZoom(100);
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " JayumintonMember/1.5");

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String scheme = request.getUrl().getScheme();
                return !("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme));
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                view.evaluateJavascript(
                        "document.documentElement.setAttribute('data-member-native-app','1');",
                        null
                );
            }
        });
        webView.loadUrl(MEMBER_URL);
    }

    private void requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                    new String[]{Manifest.permission.POST_NOTIFICATIONS},
                    REQUEST_NOTIFICATIONS
            );
        }
    }

    private void restoreSubscription() {
        String memberId = MemberStore.getSelectedMemberId(this);
        if (memberId.isEmpty()) return;
        FirebaseMessaging.getInstance()
                .subscribeToTopic(MemberStore.topicForMemberId(memberId));
    }

    private void updateSelectedMemberText() {
        String name = MemberStore.getSelectedMemberName(this);
        if (name.isEmpty()) {
            selectedMemberText.setText("알림 받을 이름이 선택되지 않았습니다.");
        } else {
            selectedMemberText.setText("내 배정 알림: " + name);
        }
    }

    private void loadMembersAndShowPicker() {
        if (webView == null) return;
        selectMemberButton.setEnabled(false);
        selectedMemberText.setText("멤버 명단을 불러오는 중...");
        webView.evaluateJavascript(READ_MEMBER_LIST_SCRIPT, value -> {
            selectMemberButton.setEnabled(true);
            List<MemberChoice> choices = parseMemberChoices(value);
            if (choices.isEmpty()) {
                updateSelectedMemberText();
                Toast.makeText(
                        MainActivity.this,
                        "사용자 페이지 로그인을 완료하고 명단이 보인 뒤 다시 눌러 주세요.",
                        Toast.LENGTH_LONG
                ).show();
                return;
            }
            showMemberPicker(choices);
        });
    }

    private List<MemberChoice> parseMemberChoices(String value) {
        List<MemberChoice> result = new ArrayList<>();
        try {
            Object decoded = new JSONTokener(value == null ? "null" : value).nextValue();
            String json = decoded instanceof String ? (String) decoded : "[]";
            JSONArray array = new JSONArray(json);
            for (int index = 0; index < array.length(); index++) {
                JSONObject item = array.optJSONObject(index);
                if (item == null) continue;
                String id = item.optString("id", "").trim();
                String name = item.optString("name", "").trim();
                if (!id.isEmpty() && !name.isEmpty()) {
                    result.add(new MemberChoice(id, name));
                }
            }
        } catch (Exception ignored) {
            result.clear();
        }

        Collator collator = Collator.getInstance(Locale.KOREA);
        result.sort((left, right) -> collator.compare(left.name, right.name));
        return result;
    }

    private void showMemberPicker(List<MemberChoice> choices) {
        String[] labels = new String[choices.size()];
        for (int index = 0; index < choices.size(); index++) {
            labels[index] = choices.get(index).name;
        }

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("알림 받을 내 이름 선택")
                .setItems(labels, null)
                .setNeutralButton("알림 해제", (ignored, which) -> clearSelection())
                .setNegativeButton("취소", null)
                .create();

        dialog.setOnShowListener(ignored -> dialog.getListView().setOnItemClickListener(
                (parent, view, position, id) -> {
                    dialog.dismiss();
                    subscribeToMember(choices.get(position));
                }
        ));
        dialog.show();
    }

    private void subscribeToMember(MemberChoice choice) {
        String oldMemberId = MemberStore.getSelectedMemberId(this);
        String oldTopic = oldMemberId.isEmpty()
                ? ""
                : MemberStore.topicForMemberId(oldMemberId);
        String newTopic = MemberStore.topicForMemberId(choice.id);

        selectedMemberText.setText(choice.name + " 알림을 설정하는 중...");
        selectMemberButton.setEnabled(false);

        FirebaseMessaging.getInstance()
                .subscribeToTopic(newTopic)
                .addOnCompleteListener(task -> runOnUiThread(() -> {
                    selectMemberButton.setEnabled(true);
                    if (!task.isSuccessful()) {
                        updateSelectedMemberText();
                        Toast.makeText(
                                MainActivity.this,
                                "알림 설정에 실패했습니다. 인터넷 연결을 확인해 주세요.",
                                Toast.LENGTH_LONG
                        ).show();
                        return;
                    }

                    MemberStore.saveSelection(MainActivity.this, choice.id, choice.name);
                    if (!oldTopic.isEmpty() && !oldTopic.equals(newTopic)) {
                        FirebaseMessaging.getInstance().unsubscribeFromTopic(oldTopic);
                    }
                    updateSelectedMemberText();
                    Toast.makeText(
                            MainActivity.this,
                            choice.name + "님의 코트 배정 알림을 받습니다.",
                            Toast.LENGTH_LONG
                    ).show();
                }));
    }

    private void clearSelection() {
        String oldMemberId = MemberStore.getSelectedMemberId(this);
        if (!oldMemberId.isEmpty()) {
            FirebaseMessaging.getInstance()
                    .unsubscribeFromTopic(MemberStore.topicForMemberId(oldMemberId));
        }
        MemberStore.clearSelection(this);
        updateSelectedMemberText();
        Toast.makeText(this, "개인 배정 알림을 해제했습니다.", Toast.LENGTH_SHORT).show();
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
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }

    private static final class MemberChoice {
        final String id;
        final String name;

        MemberChoice(String id, String name) {
            this.id = id;
            this.name = name;
        }
    }
}

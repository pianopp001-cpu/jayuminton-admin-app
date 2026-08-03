package com.jayuminton.admin;

import android.app.Activity;
import android.webkit.WebView;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

final class V199RuntimeBridge {
    private V199RuntimeBridge() {
    }

    static void install(Activity activity, WebView webView) {
        if (activity == null || webView == null) return;
        try {
            String adminRuntime = readAsset(activity, "admin-runtime.js");
            String courtRuntime = readAsset(activity, "court-orientation.js");
            String frameRepair = readAsset(activity, "frame-repair.js")
                    .replace("__JAYUMINTON_ADMIN_RUNTIME_JSON__", JSONObject.quote(adminRuntime))
                    .replace("__JAYUMINTON_COURT_ORIENTATION_JSON__", JSONObject.quote(courtRuntime));
            String pageRepair = readAsset(activity, "page-repair.js");

            webView.evaluateJavascript(pageRepair, null);
            webView.evaluateJavascript(frameRepair, null);
        } catch (Exception ignored) {
            // The court-management page must remain usable even if runtime repair fails.
        }
    }

    private static String readAsset(Activity activity, String name) throws Exception {
        try (InputStream input = activity.getAssets().open(name);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) {
                output.write(buffer, 0, count);
            }
            return output.toString(StandardCharsets.UTF_8.name());
        }
    }
}

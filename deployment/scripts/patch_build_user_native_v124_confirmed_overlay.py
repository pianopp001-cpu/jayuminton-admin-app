#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

for old, new in (
    ("v1.2.2-overlay.apk", "v1.2.4-confirmed-overlay.apk"),
    ("user-native-push-v1.2.2.txt", "user-native-push-v1.2.4.txt"),
    ('VERSION="1.2.2"', 'VERSION="1.2.4"'),
    ('VERSION_CODE="122"', 'VERSION_CODE="124"'),
    ("versionCode 122", "versionCode 124"),
    ("versionCode='122'", "versionCode='124'"),
    ("versionName '1.2.2'", "versionName '1.2.4'"),
    ("versionName='1.2.2'", "versionName='1.2.4'"),
    ('USER_APP_VERSION = "1.2.2"', 'USER_APP_VERSION = "1.2.4"'),
    ("JayumintonUserNative/1.2.2", "JayumintonUserNative/1.2.4"),
    ("JayumintonNativeAndroid/1.2.2", "JayumintonNativeAndroid/1.2.4"),
    ('APP_VERSION = "1.2.2"', 'APP_VERSION = "1.2.4"'),
    ("version=1.2.2", "version=1.2.4"),
    ("version_code=122", "version_code=124"),
    ("jayuminton_wait1_native_v122", "jayuminton_wait1_native_v124"),
    ("jayuminton_court_native_v122", "jayuminton_court_native_v124"),
):
    s = s.replace(old, new)

overlay_start = s.find("    public static boolean show(Context context, String title, String body, int notificationId) {")
overlay_end = s.find("    public static void stopEverything(Context context, int notificationId) {", overlay_start)
if overlay_start < 0 or overlay_end < 0:
    raise SystemExit("v124 overlay show method not found")

show_method = r'''    public static boolean show(Context context, String title, String body, int notificationId) {
        Context app = context.getApplicationContext();
        if (!canShow(app)) return false;
        java.util.concurrent.atomic.AtomicBoolean actuallyAdded =
                new java.util.concurrent.atomic.AtomicBoolean(false);
        java.util.concurrent.CountDownLatch finished = new java.util.concurrent.CountDownLatch(1);

        Runnable render = () -> {
            try {
                if (windowManager != null && activeView != null) {
                    try { windowManager.removeView(activeView); } catch (Exception ignored) {}
                    activeView = null;
                }
                windowManager = (WindowManager) app.getSystemService(Context.WINDOW_SERVICE);
                if (windowManager == null) return;

                LinearLayout panel = new LinearLayout(app);
                panel.setOrientation(LinearLayout.VERTICAL);
                panel.setGravity(Gravity.CENTER);
                panel.setPadding(56, 50, 56, 42);
                panel.setBackgroundColor(Color.WHITE);

                TextView heading = new TextView(app);
                heading.setText(title);
                heading.setTextSize(25);
                heading.setTextColor(Color.rgb(12, 49, 126));
                heading.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
                heading.setGravity(Gravity.CENTER);
                panel.addView(heading, new LinearLayout.LayoutParams(-1, -2));

                TextView message = new TextView(app);
                message.setText(body);
                message.setTextSize(21);
                message.setTextColor(Color.BLACK);
                message.setGravity(Gravity.CENTER);
                LinearLayout.LayoutParams messageParams = new LinearLayout.LayoutParams(-1, -2);
                messageParams.setMargins(0, 32, 0, 38);
                panel.addView(message, messageParams);

                Button confirm = new Button(app);
                confirm.setText("확인하고 닫기");
                confirm.setTextSize(19);
                confirm.setOnClickListener(view -> stopEverything(app, notificationId));
                panel.addView(confirm, new LinearLayout.LayoutParams(-1, -2));

                int type = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                        ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                        : WindowManager.LayoutParams.TYPE_PHONE;
                WindowManager.LayoutParams params = new WindowManager.LayoutParams(
                        -1, -2, type,
                        WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON |
                                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                        PixelFormat.TRANSLUCENT);
                params.gravity = Gravity.CENTER;
                windowManager.addView(panel, params);
                activeView = panel;
                actuallyAdded.set(true);
            } catch (Exception ignored) {
                activeView = null;
                actuallyAdded.set(false);
            } finally {
                finished.countDown();
            }
        };

        if (Looper.myLooper() == Looper.getMainLooper()) {
            render.run();
        } else {
            MAIN.post(render);
            try { finished.await(2500, java.util.concurrent.TimeUnit.MILLISECONDS); }
            catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); }
        }
        return actuallyAdded.get();
    }

'''
s = s[:overlay_start] + show_method + s[overlay_end:]

# Report whether the real overlay was added, rather than only whether permission existed.
old = '''        NativeDeliveryReporter.report("notification_posted", type, hasTargetMemberId,
                true, true, fullScreenAllowed, false);'''
new = '''        NativeDeliveryReporter.report("notification_posted", type,
                hasTargetMemberId, true, true, overlayShown, false);'''
if s.count(old) != 1:
    raise SystemExit("v124 overlay acknowledgement anchor missing")
s = s.replace(old, new, 1)

for marker in (
    'VERSION="1.2.4"', 'VERSION_CODE="124"',
    'AtomicBoolean(false)',
    'CountDownLatch(1)',
    'finished.await(2500',
    'windowManager.addView(panel, params)',
    'actuallyAdded.set(true)',
    'hasTargetMemberId, true, true, overlayShown, false',
    'repeatUntilConfirmed ? 0 : -1',
    '"확인하고 닫기"',
):
    if marker not in s:
        raise SystemExit("missing native v1.2.4 marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Prepared v1.2.4 with verified overlay add before repeating vibration.")

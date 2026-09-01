#!/usr/bin/env python3
"""Two bugs in the native background alert for admin direct messages:

1. JayumintonFirebaseMessagingService.showNotification() re-derives the
   full-screen alert's title from the `court` boolean alone instead of using
   the already-computed adminMessage-aware `title` argument, so an
   admin_message alert always falls into the "대기 1순위 안내" branch
   (court is false for admin messages too). Fix: pass the real title
   straight through to EXTRA_TITLE instead of recomputing it.

2. AssignmentAlertActivity (the full-screen alert shown while the app is
   backgrounded/killed) only ever renders one button, "확인하고 닫기" --
   there was never a visible "답장" button at all for admin messages, even
   though the whole point of this alert for admin_message is to let the
   member reply. Fix: when the alert is for an admin_message, show a
   second "답장" button that stops vibration, dismisses the notification,
   and opens the app (where the existing web reply UI is), in addition to
   the existing close button which also stops vibration.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

# 1) FCM service: pass adminMessage through to showNotification and stop
#    showNotification from recomputing the title from `court` alone.
call_old = '''        boolean overlayShown = AssignmentOverlay.show(this, title, body, notificationId);
        showNotification(court, title, body, assignmentId);'''
call_new = '''        boolean overlayShown = AssignmentOverlay.show(this, title, body, notificationId);
        showNotification(court, adminMessage, title, body, assignmentId);'''
if call_old not in source:
    raise SystemExit('showNotification call anchor missing')
source = source.replace(call_old, call_new, 1)

sig_old = '    private void showNotification(boolean court, String title, String body, String assignmentId) {'
sig_new = '    private void showNotification(boolean court, boolean adminMessage, String title, String body, String assignmentId) {'
if sig_old not in source:
    raise SystemExit('showNotification signature anchor missing')
source = source.replace(sig_old, sig_new, 1)

extra_title_old = '''        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_TITLE,
                (court ? "코트 입장 안내" : "대기 1순위 안내"));
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_BODY, body);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_NOTIFICATION_ID, notificationId);'''
extra_title_new = '''        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_TITLE, title);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_BODY, body);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_NOTIFICATION_ID, notificationId);
        alertIntent.putExtra(AssignmentAlertActivity.EXTRA_IS_ADMIN_MESSAGE, adminMessage);'''
if extra_title_old not in source:
    raise SystemExit('EXTRA_TITLE hardcoding anchor missing')
source = source.replace(extra_title_old, extra_title_new, 1)

emoji_old = '''        builder.setSmallIcon(R.drawable.icon)
                .setContentTitle((court ? "🚨 " : "🏸 ") + title)'''
emoji_new = '''        builder.setSmallIcon(R.drawable.icon)
                .setContentTitle((adminMessage ? "💬 " : court ? "🚨 " : "🏸 ") + title)'''
if emoji_old not in source:
    raise SystemExit('notification title emoji anchor missing')
source = source.replace(emoji_old, emoji_new, 1)

# 2) AssignmentAlertActivity: add the Intent import, the new extra constant,
#    a visible "답장" button for admin messages, and its handler.
import_old = '''import android.app.Activity;
import android.app.NotificationManager;
import android.content.Context;
import android.graphics.Color;'''
import_new = '''import android.app.Activity;
import android.app.NotificationManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;'''
if import_old not in source:
    raise SystemExit('AssignmentAlertActivity import anchor missing')
source = source.replace(import_old, import_new, 1)

const_old = '''    public static final String EXTRA_TITLE = "assignment_title";
    public static final String EXTRA_BODY = "assignment_body";
    public static final String EXTRA_NOTIFICATION_ID = "assignment_notification_id";
    private int notificationId;'''
const_new = '''    public static final String EXTRA_TITLE = "assignment_title";
    public static final String EXTRA_BODY = "assignment_body";
    public static final String EXTRA_NOTIFICATION_ID = "assignment_notification_id";
    public static final String EXTRA_IS_ADMIN_MESSAGE = "assignment_is_admin_message";
    private int notificationId;'''
if const_old not in source:
    raise SystemExit('AssignmentAlertActivity constants anchor missing')
source = source.replace(const_old, const_new, 1)

buttons_old = '''        Button confirm = new Button(this);
        confirm.setText("확인하고 닫기");
        confirm.setTextSize(18);
        confirm.setOnClickListener(view -> dismissAlert());
        panel.addView(confirm, new LinearLayout.LayoutParams(-1, -2));
        setContentView(panel);
    }'''
buttons_new = '''        boolean isAdminMessage = getIntent().getBooleanExtra(EXTRA_IS_ADMIN_MESSAGE, false);
        if (isAdminMessage) {
            Button reply = new Button(this);
            reply.setText("답장");
            reply.setTextSize(18);
            reply.setOnClickListener(view -> replyAndOpen());
            LinearLayout.LayoutParams replyParams = new LinearLayout.LayoutParams(-1, -2);
            replyParams.setMargins(0, 0, 0, 18);
            panel.addView(reply, replyParams);
        }

        Button confirm = new Button(this);
        confirm.setText(isAdminMessage ? "닫기" : "확인하고 닫기");
        confirm.setTextSize(18);
        confirm.setOnClickListener(view -> dismissAlert());
        panel.addView(confirm, new LinearLayout.LayoutParams(-1, -2));
        setContentView(panel);
    }

    private void replyAndOpen() {
        AlertVibrationController.stop(this);
        NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager != null && notificationId != 0) manager.cancel(notificationId);
        Intent open = new Intent(this, MainActivity.class);
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(open);
        finishAndRemoveTask();
    }'''
if buttons_old not in source:
    raise SystemExit('AssignmentAlertActivity buttons anchor missing')
source = source.replace(buttons_old, buttons_new, 1)

required = (
    'showNotification(court, adminMessage, title, body, assignmentId);',
    'private void showNotification(boolean court, boolean adminMessage, String title, String body, String assignmentId) {',
    'alertIntent.putExtra(AssignmentAlertActivity.EXTRA_IS_ADMIN_MESSAGE, adminMessage);',
    'import android.content.Intent;',
    'EXTRA_IS_ADMIN_MESSAGE',
    'reply.setText("답장");',
    'private void replyAndOpen() {',
    'new Intent(this, MainActivity.class)',
)
for marker in required:
    if marker not in source:
        raise SystemExit('admin-message-reply-action patch failed: ' + marker)

path.write_text(source, encoding='utf-8')
print('ADMIN_MESSAGE_REPLY_ACTION_V1_OK')

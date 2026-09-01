#!/usr/bin/env python3
"""configureAlertVolumes() ducks STREAM_MUSIC to 6 (never to 0 -- that part
was already correct) but never restored it afterward, leaving music stuck
at a low volume forever. This saves the pre-duck volume the first time it
ducks, and restores it from AlertVibrationController.stop() -- the single
choke point every confirm/dismiss path already calls -- so volume comes
back exactly when the alert (vibration) is acknowledged/stopped.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')

old_configure = '''    private void configureAlertVolumes() {
        AudioManager audio = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        if (audio == null) return;
        audio.setStreamVolume(AudioManager.STREAM_ALARM,
                audio.getStreamMaxVolume(AudioManager.STREAM_ALARM), 0);
        audio.setStreamVolume(AudioManager.STREAM_MUSIC,
                Math.min(6, audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC)), 0);
    }'''
new_configure = '''    private void configureAlertVolumes() {
        AudioManager audio = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        if (audio == null) return;
        audio.setStreamVolume(AudioManager.STREAM_ALARM,
                audio.getStreamMaxVolume(AudioManager.STREAM_ALARM), 0);
        AlertVibrationController.duckMusicVolume(this, audio);
    }'''
if old_configure not in source:
    raise SystemExit('configureAlertVolumes anchor missing')
source = source.replace(old_configure, new_configure, 1)

old_stop = '''    public static void stop(Context context) {
        final Context app = context.getApplicationContext();
        final int stoppedGeneration;
        final Vibrator captured;
        synchronized (LOCK) {
            active = false;
            generation++;
            stoppedGeneration = generation;
            if (activeRunnable != null) HANDLER.removeCallbacks(activeRunnable);
            activeRunnable = null;
            captured = activeVibrator;
            activeVibrator = null;
        }

        // First cancellation is synchronous so the button press is acted on now.
        cancelHardware(app, captured);'''
new_stop = '''    private static final String VOLUME_PREFS_NAME = "jayuminton_alert_volume";
    private static final String VOLUME_KEY_PRE_DUCK = "pre_duck_music_volume";
    private static final String VOLUME_KEY_DUCKED = "music_ducked";

    public static void duckMusicVolume(Context context, AudioManager audio) {
        Context app = context.getApplicationContext();
        android.content.SharedPreferences prefs =
                app.getSharedPreferences(VOLUME_PREFS_NAME, Context.MODE_PRIVATE);
        if (!prefs.getBoolean(VOLUME_KEY_DUCKED, false)) {
            prefs.edit()
                    .putInt(VOLUME_KEY_PRE_DUCK, audio.getStreamVolume(AudioManager.STREAM_MUSIC))
                    .putBoolean(VOLUME_KEY_DUCKED, true)
                    .apply();
        }
        audio.setStreamVolume(AudioManager.STREAM_MUSIC,
                Math.min(6, audio.getStreamMaxVolume(AudioManager.STREAM_MUSIC)), 0);
    }

    private static void restoreMusicVolume(Context app) {
        android.content.SharedPreferences prefs =
                app.getSharedPreferences(VOLUME_PREFS_NAME, Context.MODE_PRIVATE);
        if (!prefs.getBoolean(VOLUME_KEY_DUCKED, false)) return;
        int original = prefs.getInt(VOLUME_KEY_PRE_DUCK, -1);
        prefs.edit().putBoolean(VOLUME_KEY_DUCKED, false).apply();
        if (original < 0) return;
        AudioManager audio = (AudioManager) app.getSystemService(Context.AUDIO_SERVICE);
        if (audio == null) return;
        audio.setStreamVolume(AudioManager.STREAM_MUSIC, original, 0);
    }

    public static void stop(Context context) {
        final Context app = context.getApplicationContext();
        final int stoppedGeneration;
        final Vibrator captured;
        synchronized (LOCK) {
            active = false;
            generation++;
            stoppedGeneration = generation;
            if (activeRunnable != null) HANDLER.removeCallbacks(activeRunnable);
            activeRunnable = null;
            captured = activeVibrator;
            activeVibrator = null;
        }

        // First cancellation is synchronous so the button press is acted on now.
        cancelHardware(app, captured);
        restoreMusicVolume(app);'''
if old_stop not in source:
    raise SystemExit('AlertVibrationController.stop anchor missing')
source = source.replace(old_stop, new_stop, 1)

required = (
    'AlertVibrationController.duckMusicVolume(this, audio);',
    'public static void duckMusicVolume(Context context, AudioManager audio)',
    'private static void restoreMusicVolume(Context app)',
    'restoreMusicVolume(app);',
)
for marker in required:
    if marker not in source:
        raise SystemExit('volume restore patch failed: ' + marker)

path.write_text(source, encoding='utf-8')
print('VOLUME_RESTORE_V1_OK')

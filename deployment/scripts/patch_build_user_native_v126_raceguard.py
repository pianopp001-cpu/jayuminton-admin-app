#!/usr/bin/env python3
from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")

old = '''                @Override public void run() {
                    synchronized (LOCK) {
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                    }
                    Vibrator vibrator = defaultVibrator(app);
                    if (vibrator != null && vibrator.hasVibrator()) {
                        synchronized (LOCK) {
                            if (!active || generation != myGeneration || activeRunnable != this) return;
                            activeVibrator = vibrator;
                        }
                        vibrateFiniteGroup(vibrator);
                    }
                    synchronized (LOCK) {
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);
                    }
                }'''

new = '''                @Override public void run() {
                    // JAYUMINTON_V126_START_STOP_RACE_GUARD: keep the state lock
                    // across the hardware start call. A simultaneous confirmation
                    // therefore waits for vibrate() to return and cancels it after,
                    // never just before a late vibration start.
                    synchronized (LOCK) {
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        Vibrator vibrator = defaultVibrator(app);
                        if (vibrator != null && vibrator.hasVibrator()) {
                            activeVibrator = vibrator;
                            vibrateFiniteGroup(vibrator);
                        }
                        if (!active || generation != myGeneration || activeRunnable != this) return;
                        HANDLER.postDelayed(this, GROUP_REPEAT_MS);
                    }
                }'''

if s.count(old) != 1:
    raise SystemExit("v126 controller race-guard anchor missing")
s = s.replace(old, new, 1)

for marker in (
    'JAYUMINTON_V126_START_STOP_RACE_GUARD',
    'synchronized (LOCK) {',
    'vibrateFiniteGroup(vibrator);',
    'HANDLER.postDelayed(this, GROUP_REPEAT_MS);',
):
    if marker not in s:
        raise SystemExit("missing v126 race-guard marker: " + marker)

path.write_text(s, encoding="utf-8")
print("Guarded v1.2.6 against confirm racing a late vibration start.")

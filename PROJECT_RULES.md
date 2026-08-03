# Jayuminton Project Rules

## Golden Rule
Base everything on jayuminton-v199(5).apk.

## Never change
- CSS
- HTML
- Layout
- Existing v199 CSS protection logic
- WebView rendering behavior

## Only allowed change
- PIN/session token delivery for admin actions.

## Apps Script
Keep existing deployment unchanged unless explicitly requested.

## Android
Acts only as a WebView wrapper. Do not redesign the UI.

## Before every build
1. Compare against v199(5).
2. Verify no CSS/HTML changes.
3. Apply PIN-only patch.
4. Build.
5. Compare UI again.

If UI differs, discard the build.
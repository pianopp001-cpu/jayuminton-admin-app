# Member Anywhere Controls — Apps Script deployment checklist

Target branch: `member-anywhere-controls-v3`
Target PR: #28

## Files to sync into the existing Apps Script project

1. Replace `Index.html` with this branch's `source-snapshot/current-main/Index.html`.
2. Add/replace server script `MemberAnywhereSwap.js` (Apps Script editor may display the script filename without `.js`).
3. Add/replace HTML file `MemberSwapClient.html`.
4. Add/replace HTML file `MemberSwapAction.html`.
5. Add/replace HTML file `MemberControls.html`.
6. Add/replace HTML file `MemberSwapInbox.html`.

Do **not** replace `Script.html`, `Code.js`, `Admin.html`, or `Style.html` as part of this feature deployment.

`Index.html` must include, after `include('Script')`:

```html
<?!= include('MemberSwapClient'); ?>
<?!= include('MemberSwapAction'); ?>
<?!= include('MemberControls'); ?>
<?!= include('MemberSwapInbox'); ?>
```

## Safe deployment order

1. Keep the current production deployment/version intact.
2. Sync only the six files above into the Apps Script project.
3. Save all files.
4. Create a new test deployment/version rather than overwriting or deleting the known-good production deployment.
5. Open the test `/exec` URL on two member devices/sessions (A and B).
6. Only after the E2E matrix below passes should PR #28 be taken out of Draft and considered for merge/release.

## Required E2E matrix

- A requests a swap with B; B accepts; both screens converge to the swapped locations.
- B rejects; neither member moves and no normal court-assignment alert is suppressed afterward.
- Request expires after 5 minutes; neither member moves.
- A is wait group 1 / B is on a court; accepted swap must not produce a false normal court-assignment foreground alert.
- Court ↔ court swap.
- Wait ↔ wait swap.
- A or B refreshes/reopens while a request is pending; pending state is recovered.
- Attempt a second simultaneous request involving A or B; it is rejected/blocked safely.
- Change either member's position after request but before acceptance; stale snapshot acceptance fails safely.
- After a successful swap, admin/member state shows the same positions and statuses.

## Release gate

Do not merge/deploy to production merely because GitHub reports `mergeable: true`. Production release requires the real Apps Script A/B E2E matrix above to pass.

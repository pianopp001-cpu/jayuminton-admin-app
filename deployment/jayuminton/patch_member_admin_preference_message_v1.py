#!/usr/bin/env python3
"""Add member-initiated admin preference messages to the Cloudflare state worker.

The user may type only the partner name. The backend constructs the fixed Korean
sentence and stores it as a synthetic member-message reply so the existing admin
회원쪽지 panel can display/delete it without a second inbox implementation.
"""
from pathlib import Path
import sys

MARKER = "JAYUMINTON_MEMBER_ADMIN_PREFERENCE_MESSAGE_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label} anchor mismatch: {count}")
    return text.replace(old, new, 1)


def patch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return

    mutation_anchor = "export function memberDeleteMessageMutation(input, messageId, memberId) {"
    mutation = r'''/* JAYUMINTON_MEMBER_ADMIN_PREFERENCE_MESSAGE_V1
   A member can proactively ask the admin for a future pairing preference. The
   client sends only the partner name; the server owns the fixed wording so the
   request cannot be changed into arbitrary free-form text. Store it as a
   synthetic memberMessages reply with no recipients: publicState therefore
   never echoes it back as an incoming admin message, while the existing admin
   회원쪽지 panel already sees message.replies and needs no new state model. */
export function memberSendAdminPreferenceMutation(input, memberId, partnerName) {
  const state = normalizeState(input);
  const mem = String(memberId || '');
  const partner = String(partnerName || '').trim().replace(/\s+/g, ' ');
  if (!mem) throw new Error('member_identity_required');
  if (!partner) throw new Error('partner_name_required');
  if (!state.members.some(m => String(m.id) === mem)) throw new Error('member_not_found');
  const createdAt = new Date().toISOString();
  const replyItem = {
    id: `reply-${crypto.randomUUID()}`,
    memberId: mem,
    text: `대기순서 밀려도 ${partner}와 배정해 주세요.`,
    createdAt,
  };
  const item = {
    id: `msg-${crypto.randomUUID()}`,
    memberIds: [],
    text: '사용자 배정 요청',
    createdAt,
    replies: [replyItem],
    source: 'member_admin_preference',
  };
  state.memberMessages = [...state.memberMessages, item].slice(-50);
  return {
    state,
    event: {
      type: 'member_admin_preference_sent',
      messageId: item.id,
      replyId: replyItem.id,
      memberId: mem,
      partnerName: partner,
    },
  };
}

'''
    text = replace_once(text, mutation_anchor, mutation + mutation_anchor, "mutation")

    dispatch_old = "      else if (action === 'replyToMemberMessage') result = replyToMemberMessageMutation(current, body.messageId, body.memberId, body.text);\n      else if (action === 'memberDeleteMessage') result = memberDeleteMessageMutation(current, body.messageId, body.memberId);"
    dispatch_new = "      else if (action === 'replyToMemberMessage') result = replyToMemberMessageMutation(current, body.messageId, body.memberId, body.text);\n      else if (action === 'memberSendAdminPreference') result = memberSendAdminPreferenceMutation(current, body.memberId, body.partnerName);\n      else if (action === 'memberDeleteMessage') result = memberDeleteMessageMutation(current, body.messageId, body.memberId);"
    text = replace_once(text, dispatch_old, dispatch_new, "coordinator dispatch")

    names_old = "'memberAcceptPairPlay','memberRejectPairPlay','memberReplyToMessage','memberDeleteMessage'"
    names_new = "'memberAcceptPairPlay','memberRejectPairPlay','memberReplyToMessage','memberSendAdminPreference','memberDeleteMessage'"
    text = replace_once(text, names_old, names_new, "member rpc names")

    rpc_old = "    else if (name === 'memberReplyToMessage') { action = 'replyToMemberMessage'; body.messageId = String(values[2] || ''); body.memberId = memberId; body.text = String(values[3] || ''); }\n    else if (name === 'memberDeleteMessage') { action = 'memberDeleteMessage'; body.messageId = String(values[2] || ''); body.memberId = memberId; }"
    rpc_new = "    else if (name === 'memberReplyToMessage') { action = 'replyToMemberMessage'; body.messageId = String(values[2] || ''); body.memberId = memberId; body.text = String(values[3] || ''); }\n    else if (name === 'memberSendAdminPreference') { action = 'memberSendAdminPreference'; body.memberId = memberId; body.partnerName = String(values[2] || ''); }\n    else if (name === 'memberDeleteMessage') { action = 'memberDeleteMessage'; body.messageId = String(values[2] || ''); body.memberId = memberId; }"
    text = replace_once(text, rpc_old, rpc_new, "legacy member rpc")

    required = [
        MARKER,
        "memberSendAdminPreferenceMutation",
        "action === 'memberSendAdminPreference'",
        "name === 'memberSendAdminPreference'",
        "대기순서 밀려도 ${partner}와 배정해 주세요.",
        "memberIds: []",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit("member admin preference patch missing: " + needle)

    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "cloudflare/state-worker/worker.js")
    patch(target)

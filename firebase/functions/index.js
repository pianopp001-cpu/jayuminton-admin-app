"use strict";

const {onRequest} = require("firebase-functions/v2/https");
const {defineSecret} = require("firebase-functions/params");
const {initializeApp} = require("firebase-admin/app");
const {getMessaging} = require("firebase-admin/messaging");
const {createHash, timingSafeEqual} = require("node:crypto");

initializeApp();

const pushSecret = defineSecret("JAYUMINTON_PUSH_SECRET");

function topicForMemberId(memberId) {
  const hash = createHash("sha256")
      .update(String(memberId || "").trim(), "utf8")
      .digest("hex");
  return `jm_${hash}`;
}

function secretsMatch(actual, expected) {
  const left = Buffer.from(String(actual || ""), "utf8");
  const right = Buffer.from(String(expected || ""), "utf8");
  if (!left.length || left.length !== right.length) return false;
  return timingSafeEqual(left, right);
}

function cleanEvent(body) {
  const type = String(body && body.type || "court_assignment").trim();
  const assignmentId = String(body && body.assignmentId || "").trim();
  const sourceMembers = Array.isArray(body && body.members) ? body.members : [];

  if (!["court_assignment", "wait1_ready"].includes(type)) {
    throw new Error("invalid event type");
  }
  if (!/^[A-Za-z0-9_.-]{8,500}$/.test(assignmentId)) {
    throw new Error("invalid assignmentId");
  }

  const unique = new Map();
  sourceMembers.forEach((member) => {
    const id = String(member && member.id || "").trim();
    const name = String(member && member.name || "").trim();
    if (!id || !name || id.length > 200 || name.length > 80) return;
    unique.set(id, {id, name});
  });

  const members = Array.from(unique.values());
  if (members.length !== 4) {
    throw new Error("exactly four members are required");
  }

  if (type === "court_assignment") {
    const courtNo = Number(body && body.courtNo);
    if (![1, 2, 3, 4].includes(courtNo)) {
      throw new Error("invalid courtNo");
    }
    return {type, assignmentId, courtNo, members};
  }

  const expectedCourtNo = Number(body && body.expectedCourtNo);
  if (![1, 2, 3, 4].includes(expectedCourtNo)) {
    throw new Error("invalid expectedCourtNo");
  }
  return {type, assignmentId, expectedCourtNo, members};
}

exports.publishAssignment = onRequest(
    {
      region: "asia-northeast3",
      secrets: [pushSecret],
      timeoutSeconds: 30,
      memory: "256MiB",
      maxInstances: 3,
    },
    async (request, response) => {
      if (request.method !== "POST") {
        response.set("Allow", "POST").status(405).json({ok: false});
        return;
      }

      if (!secretsMatch(
          request.get("x-jayuminton-key"),
          pushSecret.value(),
      )) {
        response.status(401).json({ok: false});
        return;
      }

      let event;
      try {
        event = cleanEvent(request.body);
      } catch (error) {
        response.status(400).json({
          ok: false,
          error: String(error && error.message || "invalid request"),
        });
        return;
      }

      const messages = event.members.map((member) => {
        const data = {
          type: event.type,
          assignmentId: event.assignmentId,
          memberId: member.id,
          memberName: member.name,
        };

        if (event.type === "court_assignment") {
          data.courtNo = String(event.courtNo);
        } else {
          data.expectedCourtNo = String(event.expectedCourtNo);
        }

        return {
          topic: topicForMemberId(member.id),
          data,
          android: {
            priority: "high",
            ttl: 10 * 60 * 1000,
            collapseKey: event.assignmentId,
            restrictedPackageName: "com.jayuminton.member",
          },
        };
      });

      try {
        const results = await Promise.all(
            messages.map((message) => getMessaging().send(message)),
        );
        response.status(200).json({
          ok: true,
          type: event.type,
          assignmentId: event.assignmentId,
          sent: results.length,
        });
      } catch (error) {
        console.error("publishAssignment failed", {
          type: event.type,
          assignmentId: event.assignmentId,
          code: error && error.code,
        });
        response.status(500).json({ok: false});
      }
    },
);

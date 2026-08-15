'use strict';

const { onRequest } = require('firebase-functions/v2/https');

const MEMBER_APPS_SCRIPT_URL = process.env.MEMBER_RPC_URL || '';
const ADMIN_APPS_SCRIPT_URL = process.env.ADMIN_RPC_URL || '';

async function proxyRpc(req, res, upstreamUrl, adminMode) {
  res.set('Cache-Control', 'no-store');
  if (req.method !== 'POST') return res.status(405).json({ok:false,error:'method_not_allowed'});
  if (!upstreamUrl) return res.status(500).json({ok:false,error:'proxy_not_configured'});
  const rpc = String(req.body?.rpc || '');
  const args = Array.isArray(req.body?.args) ? req.body.args : [];
  if (!/^[A-Za-z_$][\w$]*$/.test(rpc)) return res.status(400).json({ok:false,error:'invalid_rpc'});
  const payload = Buffer.from(JSON.stringify(args), 'utf8').toString('base64url');
  const callback = adminMode ? 'jmAdminProxy' : 'jmProxy';
  const u = new URL(upstreamUrl);
  if (adminMode) u.searchParams.set('adminRpc', '1');
  u.searchParams.set('rpc', rpc);
  u.searchParams.set('callback', callback);
  u.searchParams.set('payload', payload);
  u.searchParams.set('nonce', Date.now().toString());
  try {
    const r = await fetch(u, {redirect:'follow', headers:{'Cache-Control':'no-cache'}});
    const text = await r.text();
    const prefix = callback + '(';
    if (!r.ok || !text.startsWith(prefix)) return res.status(502).json({ok:false,error:'upstream_failed',status:r.status});
    const end = text.lastIndexOf(')');
    const data = JSON.parse(text.slice(prefix.length, end));
    return res.status(200).json(data);
  } catch (e) {
    return res.status(502).json({ok:false,error:'proxy_exception',message:String(e && e.message || e)});
  }
}

exports.memberRpc = onRequest({ region: 'asia-northeast3', timeoutSeconds: 60 }, async (req, res) => {
  return proxyRpc(req, res, MEMBER_APPS_SCRIPT_URL, false);
});

exports.adminRpc = onRequest({ region: 'asia-northeast3', timeoutSeconds: 60 }, async (req, res) => {
  return proxyRpc(req, res, ADMIN_APPS_SCRIPT_URL, true);
});

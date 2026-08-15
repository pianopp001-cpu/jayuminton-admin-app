'use strict';

const { onRequest } = require('firebase-functions/v2/https');

const MEMBER_APPS_SCRIPT_URL = process.env.MEMBER_RPC_URL || '';
const ADMIN_APPS_SCRIPT_URL = process.env.ADMIN_RPC_URL || '';

async function proxyRpc(req, res, upstreamUrl, adminMode) {
  res.set('Cache-Control', 'no-store');
  const isAdminJsonp = adminMode && req.method === 'GET';
  if (req.method !== 'POST' && !isAdminJsonp) return res.status(405).json({ok:false,error:'method_not_allowed'});
  if (!upstreamUrl) return res.status(500).json({ok:false,error:'proxy_not_configured'});

  const rpc = String(isAdminJsonp ? (req.query.rpc || '') : (req.body?.rpc || ''));
  if (!/^[A-Za-z_$][\w$]*$/.test(rpc)) return res.status(400).json({ok:false,error:'invalid_rpc'});

  let args;
  let browserCallback = '';
  if (isAdminJsonp) {
    browserCallback = String(req.query.callback || '');
    if (!/^[A-Za-z_$][\w$]*$/.test(browserCallback)) return res.status(400).send('invalid_callback');
    try {
      const raw = String(req.query.payload || '');
      args = JSON.parse(Buffer.from(raw, 'base64url').toString('utf8'));
      if (!Array.isArray(args)) throw new Error('args_not_array');
    } catch (e) {
      return res.status(400).send('invalid_payload');
    }
  } else {
    args = Array.isArray(req.body?.args) ? req.body.args : [];
  }

  const payload = Buffer.from(JSON.stringify(args), 'utf8').toString('base64url');
  const upstreamCallback = adminMode ? 'jmAdminProxyUpstream' : 'jmProxy';
  const u = new URL(upstreamUrl);
  if (adminMode) u.searchParams.set('adminRpc', '1');
  u.searchParams.set('rpc', rpc);
  u.searchParams.set('callback', upstreamCallback);
  u.searchParams.set('payload', payload);
  u.searchParams.set('nonce', Date.now().toString());

  try {
    const r = await fetch(u, {redirect:'follow', headers:{'Cache-Control':'no-cache'}});
    const text = await r.text();
    const prefix = upstreamCallback + '(';
    if (!r.ok || !text.startsWith(prefix)) {
      if (isAdminJsonp) return res.status(502).type('application/javascript').send(`${browserCallback}(${JSON.stringify({ok:false,error:'upstream_failed',status:r.status})});`);
      return res.status(502).json({ok:false,error:'upstream_failed',status:r.status});
    }
    const end = text.lastIndexOf(')');
    const data = JSON.parse(text.slice(prefix.length, end));
    if (isAdminJsonp) return res.status(200).type('application/javascript').send(`${browserCallback}(${JSON.stringify(data)});`);
    return res.status(200).json(data);
  } catch (e) {
    const err = {ok:false,error:'proxy_exception',message:String(e && e.message || e)};
    if (isAdminJsonp) return res.status(502).type('application/javascript').send(`${browserCallback}(${JSON.stringify(err)});`);
    return res.status(502).json(err);
  }
}

exports.memberRpc = onRequest({ region: 'asia-northeast3', timeoutSeconds: 60 }, async (req, res) => {
  return proxyRpc(req, res, MEMBER_APPS_SCRIPT_URL, false);
});

exports.adminRpc = onRequest({ region: 'asia-northeast3', timeoutSeconds: 60 }, async (req, res) => {
  return proxyRpc(req, res, ADMIN_APPS_SCRIPT_URL, true);
});

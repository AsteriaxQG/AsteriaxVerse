const encoder=new TextEncoder();
export const json=(data,status=200,headers={})=>Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...headers}});
export const normalizeEmail=value=>String(value||'').trim().toLowerCase();
export const validEmail=email=>email.length<=254&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
export const sha256=async value=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(value))),b=>b.toString(16).padStart(2,'0')).join('');
export async function codeHash(email,code,secret){const key=await crypto.subtle.importKey('raw',encoder.encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);const sig=await crypto.subtle.sign('HMAC',key,encoder.encode(`${email}:${code}`));return Array.from(new Uint8Array(sig),b=>b.toString(16).padStart(2,'0')).join('')}
export function randomHex(size=32){const bytes=crypto.getRandomValues(new Uint8Array(size));return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')}
export function cleanIds(input){if(!Array.isArray(input)||input.length>1000)return null;const out=[],seen=new Set();for(const raw of input){if(typeof raw!=='string'&&typeof raw!=='number')return null;const id=String(raw);if(!id||id.length>100||/[\u0000-\u001f\u007f]/.test(id))return null;if(!seen.has(id)){seen.add(id);out.push(id)}}return out}
export function sameOrigin(request){const origin=request.headers.get('Origin');return origin===new URL(request.url).origin}
export function constantTimeEqual(left,right){if(typeof left!=='string'||typeof right!=='string')return false;let difference=left.length^right.length;const size=Math.max(left.length,right.length);for(let i=0;i<size;i++)difference|=(left.charCodeAt(i)||0)^(right.charCodeAt(i)||0);return difference===0}
export async function sessionFor(request,env){const token=(request.headers.get('Cookie')||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('__Host-asteriax_session='))?.slice('__Host-asteriax_session='.length);if(!token||token.length!==64)return null;const tokenHash=await sha256(token);return env.AX_DB.prepare('SELECT u.id,u.email,s.expires_at FROM ax_account_sessions s JOIN ax_account_users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?').bind(tokenHash,Date.now()).first()}
export async function issueSession(env,userId){const token=randomHex(),now=Date.now(),expires=now+30*24*60*60*1000;await env.AX_DB.prepare('INSERT INTO ax_account_sessions(token_hash,user_id,created_at,expires_at) VALUES(?,?,?,?)').bind(await sha256(token),userId,now,expires).run();return{token,expires}}
export const sessionCookie=token=>`__Host-asteriax_session=${token}; Path=/; Max-Age=2592000; Secure; HttpOnly; SameSite=Lax`;
export const expiredSessionCookie='__Host-asteriax_session=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax';



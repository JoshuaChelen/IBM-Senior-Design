import { NLIPClient, NLIPFactory } from './nlip.js';

const client = new NLIPClient(window.location.origin);

const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');
const correlator = null

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  const pair = document.createElement('div');
  pair.className = 'message-pair';

  const userBubble = document.createElement('div');
  userBubble.className = 'user-bubble';
  userBubble.textContent = message;
  pair.appendChild(userBubble);

  const botBox = document.createElement('div');
  botBox.className = 'bot-box';
  botBox.textContent = '...'; // Placeholder while waiting
  pair.appendChild(botBox);

  chatBox.appendChild(pair);
  chatBox.scrollTop = chatBox.scrollHeight;

  input.value = '';

  try {
    let data = null;
    data = await client.sendMessage(message);
    botBox.textContent =  data || 'No response';
  } catch (error) {
    botBox.textContent = 'Error connecting to chat engine.';
    console.error(error);
  }  
});


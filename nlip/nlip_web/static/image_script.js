import { NLIPClient } from './nlip.js'

const client = new NLIPClient();

const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const file = document.getElementById('file-input');
const chatBox = document.getElementById('chat-box');

file.addEventListener('change', () => {
  const fileList = document.getElementById('file-list');
  fileList.innerHTML = '';
  Array.from(file.files).forEach(f => {
    const li = document.createElement('li');
    li.textContent = f.name;
    fileList.appendChild(li);
  });
});


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
    if (file.files.length > 0) {
      data = await client.sendWithImage(message, file.files[0]);
      botBox.textContent =  data.content || 'No response';
    } else {
      data = await client.sendMessage(message);
      botBox.textContent =  data || 'No response';
    }
    
  } catch (error) {
    botBox.textContent = 'Error connecting to chat engine.';
    console.error(error);
  }  
});


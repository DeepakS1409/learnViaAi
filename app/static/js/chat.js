// Padika AI — Chatbot Glassmorphism Engine

document.addEventListener('DOMContentLoaded', () => {
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const messagesContainer = document.getElementById('chatMessages');
  const sendBtn = document.getElementById('chatSendBtn');
  const subjectSelect = document.getElementById('subjectSelect');
  const documentSelect = document.getElementById('documentSelect');
  const languageSelect = document.getElementById('languageSelect');
  const newChatBtn = document.getElementById('newChatBtn');

  let activeFormat = 'normal';
  let isSubmitting = false;

  // Format pill toggles
  document.querySelectorAll('.format-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.format-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeFormat = pill.getAttribute('data-format') || 'normal';
    });
  });

  // Auto-resize chat input
  if (chatInput) {
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });

    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitMessage();
      }
    });
  }

  // Handle Form Submit
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      submitMessage();
    });
  }

  // Handle Suggestion Clicks
  document.querySelectorAll('.suggestion-card').forEach(card => {
    card.addEventListener('click', () => {
      const prompt = card.getAttribute('data-prompt');
      const format = card.getAttribute('data-format');
      const lang = card.getAttribute('data-lang');
      const sub = card.getAttribute('data-subject');

      if (prompt && chatInput) {
        chatInput.value = prompt;
        if (format) {
          activeFormat = format;
          document.querySelectorAll('.format-pill').forEach(p => {
            p.classList.toggle('active', p.getAttribute('data-format') === format);
          });
        }
        if (lang && languageSelect) languageSelect.value = lang;
        if (sub && subjectSelect) subjectSelect.value = sub;
        submitMessage();
      }
    });
  });

  // New Chat Button
  if (newChatBtn) {
    newChatBtn.addEventListener('click', async () => {
      try {
        const resp = await fetch('/chat/api/sessions/new', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: 'New Discussion',
            subject_id: subjectSelect ? subjectSelect.value : null,
            material_id: documentSelect ? documentSelect.value : null,
            language: languageSelect ? languageSelect.value : 'en',
            format: activeFormat
          })
        });
        const data = await resp.json();
        if (data.success) {
          window.location.href = `/chat?session_id=${data.session_id}`;
        }
      } catch (err) {
        console.error('Failed to create new session:', err);
      }
    });
  }

  // Delete session handler
  document.querySelectorAll('.session-delete-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const sessId = btn.getAttribute('data-session-id');
      if (!sessId || !confirm('Are you sure you want to delete this chat session?')) return;

      try {
        const resp = await fetch(`/chat/api/sessions/${sessId}`, { method: 'DELETE' });
        const data = await resp.json();
        if (data.success) {
          btn.closest('.chat-session-item').remove();
          // If deleted session was active, redirect to /chat
          const urlParams = new URLSearchParams(window.location.search);
          if (urlParams.get('session_id') === sessId) {
            window.location.href = '/chat';
          }
        }
      } catch (err) {
        console.error('Failed to delete session:', err);
      }
    });
  });

  // Scroll to bottom on load
  scrollToBottom();

  async function submitMessage() {
    if (isSubmitting) return;
    const text = chatInput.value.trim();
    if (!text) return;

    isSubmitting = true;
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Remove welcome screen if present
    const welcome = document.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    // 1. Append User Message Bubble
    appendUserBubble(text);
    scrollToBottom();

    // 2. Append AI Typing Indicator
    const typingId = appendTypingIndicator();
    scrollToBottom();

    // 3. Make API call
    const currentSessionId = document.getElementById('activeSessionId')?.value;
    const payload = {
      message: text,
      session_id: currentSessionId || null,
      subject_id: subjectSelect?.value ? parseInt(subjectSelect.value) : null,
      material_id: documentSelect?.value ? parseInt(documentSelect.value) : null,
      language: languageSelect?.value || 'en',
      format: activeFormat
    };

    try {
      const resp = await fetch('/chat/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();

      // Remove typing indicator
      removeTypingIndicator(typingId);

      if (data.success) {
        appendAIBubble(data.answer, data.citations, data.grounded);
        if (data.session_id && (!currentSessionId || currentSessionId !== String(data.session_id))) {
          const sessInput = document.getElementById('activeSessionId');
          if (sessInput) sessInput.value = data.session_id;
          // Update URL without reload
          window.history.replaceState({}, '', `/chat?session_id=${data.session_id}`);
        }
      } else {
        appendAIBubble(`⚠️ Error: ${data.error || 'Unable to generate response.'}`, []);
      }
    } catch (err) {
      console.error('Chat error:', err);
      removeTypingIndicator(typingId);
      appendAIBubble('⚠️ Network error or connection dropped. Please try again.', []);
    } finally {
      isSubmitting = false;
      sendBtn.disabled = false;
      scrollToBottom();
      chatInput.focus();
    }
  }

  function appendUserBubble(text) {
    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `
      <div class="message-avatar user-avatar-badge">You</div>
      <div class="message-bubble">${escapeHtml(text)}</div>
    `;
    messagesContainer.appendChild(row);
  }

  function appendTypingIndicator() {
    const id = 'typing-' + Date.now();
    const row = document.createElement('div');
    row.className = 'message-row ai';
    row.id = id;
    row.innerHTML = `
      <div class="message-avatar ai-avatar-badge">✦</div>
      <div class="message-bubble" style="padding: 12px 18px;">
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
    return id;
  }

  function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function appendAIBubble(markdownText, citations = [], grounded = true) {
    const row = document.createElement('div');
    row.className = 'message-row ai';

    const formattedContent = renderMarkdown(markdownText);
    let citationsHtml = '';

    if (citations && citations.length > 0) {
      citationsHtml = `
        <div class="citations-wrapper">
          <div class="citations-header">📚 Faculty Sources & Citations:</div>
          <div class="citations-grid">
            ${citations.map(c => `
              <a href="/materials/${c.material_id}/view#page=${c.page_number}" target="_blank" class="citation-card" title="${c.snippet}">
                <span>📄 ${escapeHtml(c.document_title)}</span>
                <span class="citation-page-badge">Page ${c.page_number}</span>
              </a>
            `).join('')}
          </div>
        </div>
      `;
    }

    const uniqueId = 'ans-' + Date.now();

    row.innerHTML = `
      <div class="message-avatar ai-avatar-badge">✦</div>
      <div class="message-bubble">
        <div class="message-text" id="${uniqueId}">${formattedContent}</div>
        ${citationsHtml}
        <div class="message-actions">
          <button class="msg-action-btn" onclick="copyAnswerText('${uniqueId}', this)">
            <span>📋 Copy Answer</span>
          </button>
        </div>
      </div>
    `;
    messagesContainer.appendChild(row);
  }

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  // Markdown renderer for academic answers
  function renderMarkdown(md) {
    if (!md) return '';
    let html = md;

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold & Italics
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

    // Blockquotes
    html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Code blocks & inline code
    html = html.replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>');
    html = html.replace(/`([^`]+)`/gim, '<code>$1</code>');

    // Bullet lists
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
    // Clean up multiple consecutive <ul> tags
    html = html.replace(/<\/ul>\s*<ul>/gim, '');

    // Numbered lists
    html = html.replace(/^\d+\.\s+(.*$)/gim, '<li>$1</li>');

    // Line breaks
    html = html.replace(/\n\n/gim, '<br><br>');
    return html;
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});

// Global copy answer function
function copyAnswerText(elementId, btn) {
  const el = document.getElementById(elementId);
  if (el) {
    const text = el.innerText;
    copyToClipboard(text, btn);
  }
}


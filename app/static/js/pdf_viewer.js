// Padika AI — PDF Reader & Assistant Engine

document.addEventListener('DOMContentLoaded', () => {
  const toggleAiBtn = document.getElementById('toggleAiBtn');
  const aiDrawer = document.getElementById('pdfAiDrawer');
  const closeAiDrawer = document.getElementById('closeAiDrawer');
  const pdfAiForm = document.getElementById('pdfAiForm');
  const pdfAiInput = document.getElementById('pdfAiInput');
  const pdfAiMessages = document.getElementById('pdfAiMessages');
  const materialId = document.getElementById('currentMaterialId')?.value;
  const fullscreenBtn = document.getElementById('fullscreenBtn');

  // Toggle AI Drawer
  if (toggleAiBtn && aiDrawer) {
    toggleAiBtn.addEventListener('click', () => {
      aiDrawer.classList.toggle('collapsed');
      if (!aiDrawer.classList.contains('collapsed') && pdfAiInput) {
        pdfAiInput.focus();
      }
    });
  }

  if (closeAiDrawer && aiDrawer) {
    closeAiDrawer.addEventListener('click', () => {
      aiDrawer.classList.add('collapsed');
    });
  }

  // Fullscreen Toggle
  if (fullscreenBtn) {
    fullscreenBtn.addEventListener('click', () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
          console.error(err);
        });
      } else {
        document.exitFullscreen();
      }
    });
  }

  // Quick Q&A submission targeting this specific document
  if (pdfAiForm && pdfAiInput && materialId) {
    pdfAiForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = pdfAiInput.value.trim();
      if (!question) return;

      pdfAiInput.value = '';

      // User message
      const userMsg = document.createElement('div');
      userMsg.style.alignSelf = 'flex-end';
      userMsg.style.background = 'linear-gradient(135deg, rgba(168, 85, 247, 0.4), rgba(99, 102, 241, 0.4))';
      userMsg.style.padding = '10px 14px';
      userMsg.style.borderRadius = '12px';
      userMsg.style.fontSize = '0.9rem';
      userMsg.style.maxWidth = '85%';
      userMsg.innerText = question;
      pdfAiMessages.appendChild(userMsg);
      pdfAiMessages.scrollTop = pdfAiMessages.scrollHeight;

      // Loading bubble
      const loading = document.createElement('div');
      loading.style.alignSelf = 'flex-start';
      loading.style.background = 'rgba(255, 255, 255, 0.05)';
      loading.style.padding = '10px 14px';
      loading.style.borderRadius = '12px';
      loading.style.fontSize = '0.85rem';
      loading.style.color = '#c4b5fd';
      loading.innerText = 'Searching document & analyzing...';
      pdfAiMessages.appendChild(loading);
      pdfAiMessages.scrollTop = pdfAiMessages.scrollHeight;

      try {
        const resp = await fetch('/chat/api/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: question,
            material_id: parseInt(materialId),
            format: 'normal'
          })
        });
        const data = await resp.json();
        loading.remove();

        const aiMsg = document.createElement('div');
        aiMsg.style.alignSelf = 'flex-start';
        aiMsg.style.background = 'rgba(26, 19, 58, 0.85)';
        aiMsg.style.border = '1px solid rgba(255, 255, 255, 0.12)';
        aiMsg.style.padding = '12px 14px';
        aiMsg.style.borderRadius = '12px';
        aiMsg.style.fontSize = '0.88rem';
        aiMsg.style.lineHeight = '1.5';
        aiMsg.style.maxWidth = '90%';

        let citationsSnippet = '';
        if (data.citations && data.citations.length > 0) {
          citationsSnippet = `<div style="margin-top: 8px; font-size: 0.75rem; color: #a78bfa;">📑 Page references: ${data.citations.map(c => `Page ${c.page_number}`).join(', ')}</div>`;
        }

        aiMsg.innerHTML = `<div>${data.answer.replace(/\n/g, '<br>')}</div>${citationsSnippet}`;
        pdfAiMessages.appendChild(aiMsg);
        pdfAiMessages.scrollTop = pdfAiMessages.scrollHeight;
      } catch (err) {
        console.error('Quick AI error:', err);
        loading.innerText = '⚠️ Error analyzing document.';
      }
    });
  }
});


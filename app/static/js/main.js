// Padika AI — Core Client Interactions

document.addEventListener('DOMContentLoaded', () => {
  // 1. Flash alert dismiss
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.glass-alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 2. Global Bookmark Toggle
  document.querySelectorAll('.bookmark-toggle-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const materialId = btn.getAttribute('data-material-id');
      if (!materialId) return;

      try {
        const resp = await fetch('/student/api/bookmark/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ material_id: parseInt(materialId) })
        });
        const data = await resp.json();
        if (data.success) {
          const isSaved = data.is_bookmarked;
          btn.classList.toggle('active', isSaved);
          const icon = btn.querySelector('.bookmark-icon');
          if (icon) {
            icon.textContent = isSaved ? '★' : '☆';
          }
          btn.setAttribute('title', isSaved ? 'Bookmarked' : 'Add bookmark');
          showToast(isSaved ? 'Material bookmarked!' : 'Bookmark removed.', 'info');
        }
      } catch (err) {
        console.error('Bookmark error:', err);
      }
    });
  });

  // 3. Modals open/close
  document.querySelectorAll('[data-modal-target]').forEach(trigger => {
    trigger.addEventListener('click', () => {
      const modalId = trigger.getAttribute('data-modal-target');
      const modal = document.getElementById(modalId);
      if (modal) modal.classList.add('active');
    });
  });

  document.querySelectorAll('.modal-close-btn, .glass-modal-overlay').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target === el || e.target.classList.contains('modal-close-btn')) {
        const modal = el.closest('.glass-modal-overlay') || el;
        modal.classList.remove('active');
      }
    });
  });
});

// Toast notification helper
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.position = 'fixed';
    toastContainer.style.bottom = '24px';
    toastContainer.style.right = '24px';
    toastContainer.style.zIndex = '9999';
    toastContainer.style.display = 'flex';
    toastContainer.style.flexDirection = 'column';
    toastContainer.style.gap = '8px';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = `glass-alert glass-alert-${type}`;
  toast.style.margin = '0';
  toast.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5)';
  toast.innerHTML = `<span>${message}</span>`;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

// Copy to clipboard helper
function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', 'success');
    if (btnElement) {
      const originalText = btnElement.innerText;
      btnElement.innerText = 'Copied!';
      setTimeout(() => { btnElement.innerText = originalText; }, 1800);
    }
  }).catch(err => {
    console.error('Copy failed', err);
  });
}


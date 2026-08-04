// messages.js - minimal interaction logic
// Behaviors:
// - Mobile sidebar toggle
// - Simple client-side search/filter for conversations
// - Keyboard navigation (arrow up/down) in conversation list
// - Auto-resize textarea and Enter-to-send (shift+enter for newline)
// - Placeholder for infinite scroll and auto-scroll

document.addEventListener('DOMContentLoaded', function(){
  // Mobile sidebar drawer
  const mobileBtn = document.getElementById('mobile-open-sidebar');
  let drawer;
  if(mobileBtn){
    drawer = document.createElement('div');
    drawer.className = 'mobile-sidebar-drawer p-3';
    drawer.setAttribute('role','dialog');
    drawer.innerHTML = document.querySelector('.sidebar-card').outerHTML;
    document.body.appendChild(drawer);

    mobileBtn.addEventListener('click', ()=>{ drawer.classList.add('open'); document.body.style.overflow='hidden'; });
    drawer.addEventListener('click', (ev)=>{ if(ev.target===drawer) { drawer.classList.remove('open'); document.body.style.overflow=''; } });
  }

  // Conversation search (client-side filter)
  const searchInput = document.getElementById('messages-search');
  if(searchInput){
    const list = document.getElementById('convo-list');
    const clearBtn = document.getElementById('clear-search');
    searchInput.addEventListener('input', function(){
      const q = this.value.trim().toLowerCase();
      if(clearBtn) clearBtn.style.display = q ? 'block' : 'none';
      if(!list) return;
      Array.from(list.children).forEach(item => {
        const name = item.querySelector('.conversation-name')?.textContent?.toLowerCase() || '';
        const preview = item.querySelector('.conversation-preview')?.textContent?.toLowerCase() || '';
        item.style.display = (name.indexOf(q) !== -1 || preview.indexOf(q)!==-1) ? '' : 'none';
      });
    });
    if(clearBtn){ clearBtn.addEventListener('click', ()=>{ searchInput.value=''; searchInput.dispatchEvent(new Event('input')); clearBtn.style.display='none'; }); }
  }

  // Keyboard navigation for conversation list
  const convoList = document.getElementById('convo-list');
  if(convoList){
    let index = 0;
    const items = () => Array.from(convoList.querySelectorAll('.convo-card')).filter(i=>i.style.display!=='none');
    convoList.addEventListener('keydown', (e)=>{
      const visible = items();
      if(!visible.length) return;
      if(e.key === 'ArrowDown'){ e.preventDefault(); index = Math.min(index+1, visible.length-1); visible[index].focus(); }
      if(e.key === 'ArrowUp'){ e.preventDefault(); index = Math.max(index-1, 0); visible[index].focus(); }
      if(e.key === 'Enter'){ visible[index].click(); }
    });
  }

  // Message composer behaviors
  const textarea = document.getElementById('message-text');
  const form = document.getElementById('message-form');
  if(textarea){
    textarea.addEventListener('input', ()=>{ textarea.style.height='auto'; textarea.style.height = (textarea.scrollHeight)+'px'; });
    textarea.addEventListener('keydown', (e)=>{
      if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); document.getElementById('send-btn').click(); }
    });
  }

  if(form){
    form.addEventListener('submit', (e)=>{
      e.preventDefault();
      const text = textarea.value.trim();
      if(!text) return;
      // Minimal optimistic UI: append a local outgoing bubble
      const msgs = document.getElementById('messages-area');
      const wrapper = document.createElement('div'); wrapper.className='new-message';
      wrapper.innerHTML = `\n        <div class="message-row d-flex justify-content-end mb-2">\n          <div class="message-bubble outgoing">\n            <div class="message-content">${escapeHtml(text).replace(/\n/g,'<br>')}</div>\n            <div class="message-meta d-flex align-items-center gap-2 small text-muted mt-1">\n              <span class="message-time">Now</span>\n              <i class="bi bi-check2" aria-label="Sent"></i>\n            </div>\n          </div>\n        </div>\n      `;
      msgs.appendChild(wrapper);
      msgs.scrollTop = msgs.scrollHeight;
      textarea.value=''; textarea.style.height='auto';

      // TODO: send message via existing form or websocket — keep backend unchanged
    });
  }

  // Auto-scroll helper
  const messagesArea = document.getElementById('messages-area');
  if(messagesArea){ messagesArea.scrollTop = messagesArea.scrollHeight; }

  // Utility: escape HTML
  function escapeHtml(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace("'","&#39;"); }

});

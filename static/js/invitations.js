// Minimal JS for invitations page
// - character counter for textarea
// - small animations for send button (loading state)

document.addEventListener('DOMContentLoaded', function(){
  const textarea = document.getElementById('invite-message');
  const counter = document.getElementById('char-count');
  const form = document.getElementById('send-invite-form');
  const sendBtn = document.getElementById('send-invite-btn');
  const MAX = 500;

  if(textarea && counter){
    textarea.addEventListener('input', ()=>{
      const len = textarea.value.length;
      counter.textContent = `${len} / ${MAX}`;
      if(len>MAX) counter.classList.add('text-danger'); else counter.classList.remove('text-danger');
    });
  }

  if(form && sendBtn){
    form.addEventListener('submit', ()=>{
      sendBtn.disabled = true;
      sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Sending...';
    });
  }
});
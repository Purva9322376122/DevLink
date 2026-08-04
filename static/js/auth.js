// auth.js - password toggle, theme toggle, form loading state
(function(){
  // Password toggle using Bootstrap Icons
  function togglePassword(btn){
    const target = document.querySelector(btn.dataset.target);
    if(!target) return;
    const icon = btn.querySelector('i');
    const isPassword = target.type === 'password';
    target.type = isPassword ? 'text' : 'password';
    if(icon){
      icon.classList.remove(isPassword ? 'bi-eye-slash' : 'bi-eye');
      icon.classList.add(isPassword ? 'bi-eye' : 'bi-eye-slash');
    }
    // subtle scale animation
    try{ btn.animate([{transform:'scale(1.0)'},{transform:'scale(1.05)'},{transform:'scale(1.0)'}],{duration:140}); }catch(e){}
  }

  document.querySelectorAll('.password-toggle').forEach(btn=>{
    btn.addEventListener('click', ()=> togglePassword(btn));
  });

  // Remove legacy social handlers (no-op if no social buttons)
  document.querySelectorAll('.btn-social').forEach(el=>{
    el.addEventListener('click', function(e){
      if(this.getAttribute('href') === '#'){
        e.preventDefault();
      }
    });
  });

  // Theme toggle
  const themeToggleButtons = document.querySelectorAll('#theme-toggle');
  function applyTheme(theme){
    try{ localStorage.setItem('dl-theme', theme); }catch(e){}
    if(theme==='dark') document.documentElement.setAttribute('data-theme','dark');
    else document.documentElement.removeAttribute('data-theme');
  }
  // init
  const saved = localStorage.getItem('dl-theme')||'light';
  applyTheme(saved);
  themeToggleButtons.forEach(btn=> btn.addEventListener('click', ()=>{
    const cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    applyTheme(cur === 'dark' ? 'light' : 'dark');
  }));

  // Button loading state
  document.querySelectorAll('form').forEach(form=>{
    form.addEventListener('submit', function(e){
      const btn = form.querySelector('button[type=submit]');
      if(btn){
        const txt = btn.getAttribute('data-loading-text') || 'Loading...';
        btn.disabled = true;
        btn.dataset.prevText = btn.innerHTML;
        btn.innerHTML = txt;
      }
    });
  });

  // Simple client-side validation visual feedback
  document.querySelectorAll('.form-input').forEach(input=>{
    input.addEventListener('input', ()=>{
      if(!input.checkValidity()){
        input.classList.remove('valid'); input.classList.add('invalid');
      } else {
        input.classList.remove('invalid'); input.classList.add('valid');
      }
    });
  });
})();
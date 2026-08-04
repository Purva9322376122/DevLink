// Global UI behaviors for components
document.addEventListener('DOMContentLoaded', function(){
  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e){
    var open = document.querySelectorAll('.dl-dropdown.show');
    open.forEach(function(el){
      if(!el.contains(e.target)){
        el.classList.remove('show');
      }
    });
  });

  // Simple accessible toggles for elements with data-dl-toggle
  document.querySelectorAll('[data-dl-toggle]').forEach(function(btn){
    btn.addEventListener('click', function(e){
      var target = document.querySelector(btn.getAttribute('data-dl-toggle'));
      if(!target) return;
      var visible = target.classList.toggle('d-none');
      btn.setAttribute('aria-expanded', visible ? 'true' : 'false');
    });
  });

  // Simple toast utility
  window.dlToast = function(message, type){
    var container = document.getElementById('dl-toast-container');
    if(!container){
      container = document.createElement('div'); container.id='dl-toast-container'; container.className='dl-toast-container'; document.body.appendChild(container);
    }
    var t = document.createElement('div'); t.className='dl-toast dl-toast-'+(type||'info'); t.textContent = message; container.appendChild(t);
    setTimeout(function(){ t.classList.add('visible'); }, 10);
    setTimeout(function(){ t.classList.remove('visible'); setTimeout(function(){ t.remove(); },300); }, 4500);
  };
});

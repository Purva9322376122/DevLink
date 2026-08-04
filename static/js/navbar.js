// navbar.js - adds shadow on scroll, mobile toggle, badge formatting, and accessibility hooks
(function(){
  const nav = document.getElementById('main-navbar');
  if(!nav) return;

  function onScroll(){
    if(window.scrollY > 8){
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  }
  onScroll();
  window.addEventListener('scroll', onScroll, {passive:true});

  // Mobile toggle: show/hide .dl-nav
  const toggle = document.getElementById('dl-mobile-toggle');
  const navList = document.querySelector('.dl-nav');
  if(toggle && navList){
    toggle.addEventListener('click', function(){
      const expanded = this.getAttribute('aria-expanded') === 'true';
      this.setAttribute('aria-expanded', String(!expanded));
      navList.classList.toggle('open');
    });

    // close when clicking outside on small screens
    document.addEventListener('click', function(e){
      if(window.innerWidth > 991) return;
      if(!nav.contains(e.target) && navList.classList.contains('open')){
        navList.classList.remove('open');
        toggle.setAttribute('aria-expanded','false');
      }
    });
  }

  // Close mobile menu on resize > 991
  window.addEventListener('resize', function(){
    if(window.innerWidth > 991 && navList && navList.classList.contains('open')){
      navList.classList.remove('open');
      if(toggle) toggle.setAttribute('aria-expanded','false');
    }
  });

  // Cap notification badges to "99+"
  function capBadge(el){
    if(!el) return;
    const v = parseInt(el.textContent||el.innerText||0,10);
    if(!isNaN(v) && v>99){ el.textContent='99+'; }
  }
  capBadge(document.getElementById('notif-badge'));
  document.querySelectorAll('.dl-notif').forEach(capBadge);

  // Keyboard: allow Esc to close mobile nav
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape'){
      if(navList && navList.classList.contains('open')){
        navList.classList.remove('open');
        if(toggle) toggle.setAttribute('aria-expanded','false');
      }
    }
  });

  // Dropdown handling (profile, notifications)
  (function(){
    const dropdowns = document.querySelectorAll('.dl-dropdown');
    if(!dropdowns) return;

    function closeAll(except){
      dropdowns.forEach(d => {
        if(d === except) return;
        d.classList.remove('open');
        const btn = d.querySelector('button');
        if(btn) btn.setAttribute('aria-expanded','false');
      });
    }

    document.addEventListener('click', function(e){
      let clickedDropdown = null;
      dropdowns.forEach(d => {
        const btn = d.querySelector('button');
        const menu = d.querySelector('.dl-dropdown-menu');
        if(btn && btn.contains(e.target)){
          // toggle
          const isOpen = d.classList.toggle('open');
          btn.setAttribute('aria-expanded', String(isOpen));
          clickedDropdown = d;

          // focus management when opening
          if(isOpen && menu){
            // focus first focusable item inside menu
            const focusable = menu.querySelectorAll('a[role="menuitem"], button[role="menuitem"], [role="menuitem"]');
            if(focusable.length){
              focusable[0].setAttribute('tabindex','0');
              focusable[0].focus();
            }
          }
        }
      });

      if(!clickedDropdown){
        // click outside -> close all
        let insideAny = false;
        dropdowns.forEach(d => {
          if(d.contains(e.target)) insideAny = true;
        });
        if(!insideAny) closeAll();
      } else {
        // close others
        closeAll(clickedDropdown);
      }
    });

    // Keyboard navigation for open dropdowns
    document.addEventListener('keydown', function(e){
      // find currently open dropdown
      const openDropdown = Array.from(dropdowns).find(d => d.classList.contains('open'));
      if(!openDropdown) return;
      const menu = openDropdown.querySelector('.dl-dropdown-menu');
      if(!menu) return;

      const items = Array.from(menu.querySelectorAll('a[role="menuitem"], button[role="menuitem"], [role="menuitem"]'));
      if(!items.length) return;

      const activeEl = document.activeElement;
      const idx = items.indexOf(activeEl);

      if(e.key === 'Escape'){
        closeAll();
        const btn = openDropdown.querySelector('button'); if(btn) btn.focus();
        return;
      }

      if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
        e.preventDefault();
        let nextIndex = 0;
        if(e.key === 'ArrowDown') nextIndex = (idx + 1) % items.length;
        if(e.key === 'ArrowUp') nextIndex = (idx - 1 + items.length) % items.length;
        if(e.key === 'Home') nextIndex = 0;
        if(e.key === 'End') nextIndex = items.length - 1;
        items[nextIndex].focus();
        return;
      }

      if(e.key === 'Enter' || e.key === ' '){
        // activate the focused item
        if(activeEl && (activeEl.tagName === 'A' || activeEl.tagName === 'BUTTON')){
          activeEl.click();
        }
      }
    });

    // Close on resize (prevent misplacement)
    window.addEventListener('resize', function(){ closeAll(); });
  })();
})();

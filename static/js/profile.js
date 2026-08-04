// profile.js - image preview for profile edit
(function(){
  const fileInput = document.getElementById('id_profile_image');
  const fileNameEl = document.getElementById('fileName');
  const avatarPreview = document.getElementById('avatarPreview');
  if(!fileInput) return;

  fileInput.addEventListener('change', function(e){
    const file = this.files && this.files[0];
    if(!file){
      fileNameEl && (fileNameEl.textContent = 'No file chosen');
      return;
    }
    fileNameEl && (fileNameEl.textContent = file.name);

    if(file.type && file.type.startsWith('image/')){
      const reader = new FileReader();
      reader.onload = function(ev){
        if(avatarPreview){
          if(avatarPreview.tagName.toLowerCase() === 'img'){
            avatarPreview.src = ev.target.result;
          } else {
            // placeholder div -> convert to img
            const img = document.createElement('img');
            img.id = 'avatarPreview';
            img.className = 'avatar-img';
            img.src = ev.target.result;
            avatarPreview.replaceWith(img);
          }
        }
      };
      reader.readAsDataURL(file);
    }
  });
})();

// profile view: contribution graph and activity toggles
(function(){
  const dataContainer = document.getElementById('contribution-data');
  const graph = document.getElementById('contribution-graph');
  const totalEl = document.getElementById('contribution-total');
  const selectedYearEl = document.getElementById('selected-year');
  const activeDaysEl = document.getElementById('active-days');
  const currentStreakEl = document.getElementById('current-streak');
  const streakEl = document.getElementById('max-streak');
  const yearList = document.getElementById('contribution-year-list');
  if(dataContainer && graph && totalEl){
    const allDates = Array.from(dataContainer.querySelectorAll('[data-date]')).map(el=>el.getAttribute('data-date')).filter(Boolean);
    const countByDate = {};
    allDates.forEach(d=>countByDate[d] = (countByDate[d]||0)+1);
    const fmt = d=>{const y=d.getFullYear();const m=String(d.getMonth()+1).padStart(2,'0');const day=String(d.getDate()).padStart(2,'0');return `${y}-${m}-${day}`};
    const colorFor = c=>{ if(c<=0) return '#ebedf0'; if(c===1) return '#9be9a8'; if(c===2) return '#40c463'; if(c<=4) return '#30a14e'; return '#216e39'};
    const yearsWithData = Array.from(new Set(allDates.map(dt=>Number(dt.slice(0,4))).filter(y=>Number.isFinite(y))));
    const currentYear = new Date().getFullYear();
    const minYear = yearsWithData.length ? Math.min(...yearsWithData) : currentYear;
    const years = [];
    for(let y=currentYear;y>=minYear;y--) years.push(y);
    if(!years.length) years.push(currentYear);

    const renderYear = (selectedYear)=>{
      graph.innerHTML='';
      if(selectedYearEl) selectedYearEl.textContent = selectedYear;
      const yearStart = new Date(selectedYear,0,1);
      const yearEnd = new Date(selectedYear,11,31);
      const startWeekDay = yearStart.getDay();
      const gridStart = new Date(yearStart); gridStart.setDate(yearStart.getDate()-startWeekDay);
      const endWeekDay = yearEnd.getDay();
      const gridEnd = new Date(yearEnd); gridEnd.setDate(yearEnd.getDate()+(6-endWeekDay));
      const days=[]; for(let d=new Date(gridStart); d<=gridEnd; d.setDate(d.getDate()+1)) days.push(new Date(d));

      let totalContributions=0, activeDays=0, maxStreak=0, currentRun=0, latestStreak=0;
      for(let i=0;i<366;i++){ const d=new Date(yearStart); d.setDate(yearStart.getDate()+i); if(d>yearEnd) break; const key=fmt(d); const count = countByDate[key]||0; totalContributions+=count; if(count>0){ activeDays++; currentRun++; if(currentRun>maxStreak) maxStreak=currentRun;} else {currentRun=0;} latestStreak = currentRun; }
      if(totalEl) totalEl.textContent = totalContributions; if(activeDaysEl) activeDaysEl.textContent = activeDays; if(currentStreakEl) currentStreakEl.textContent = latestStreak; if(streakEl) streakEl.textContent = maxStreak;

      const monthLabels=[]; const seenMonths=new Set(); days.forEach((d, idx)=>{ if(d<yearStart||d>yearEnd) return; const key=`${d.getFullYear()}-${d.getMonth()}`; if(d.getDate()<=7 && !seenMonths.has(key)){ seenMonths.add(key); monthLabels.push({month:d.toLocaleString('default',{month:'short'}),col:Math.floor(idx/7)}); } });
      const monthRow = document.createElement('div'); monthRow.className='month-row'; monthRow.style.display='flex'; monthRow.style.gap='2px';
      const totalCols = Math.ceil(days.length/7);
      for(let c=0;c<totalCols;c++){ const label = monthLabels.find(m=>m.col===c); const cell=document.createElement('div'); cell.className='month-cell'; cell.style.width='12px'; cell.style.fontSize='10px'; cell.textContent = label?label.month:''; monthRow.appendChild(cell); }

      const wrapper=document.createElement('div'); wrapper.className='contrib-wrapper'; wrapper.style.display='flex'; wrapper.style.gap='6px';
      const yLabels=document.createElement('div'); yLabels.className='y-labels'; yLabels.style.display='grid'; yLabels.style.gridTemplateRows='repeat(7, 12px)'; yLabels.style.gap='4px'; ['Sun','','Tue','','Thu','','Sat'].forEach(day=>{ const el=document.createElement('div'); el.className='day-label'; el.style.fontSize='10px'; el.textContent=day; yLabels.appendChild(el); });
      const grid=document.createElement('div'); grid.className='contrib-grid'; grid.style.display='grid'; grid.style.gridAutoFlow='column'; grid.style.gridAutoRows='12px'; grid.style.gap='4px';
      days.forEach(d=>{ const key=fmt(d); const count = countByDate[key]||0; const inRange = d>=yearStart && d<=yearEnd; const cell = document.createElement('div'); cell.style.width='12px'; cell.style.height='12px'; cell.style.borderRadius='2px'; cell.style.backgroundColor = inRange ? colorFor(count) : 'transparent'; if(inRange){ cell.title = `${count} contribution${count===1?'':'s'} on ${key}`; } grid.appendChild(cell); });
      graph.appendChild(monthRow); wrapper.appendChild(yLabels); wrapper.appendChild(grid); graph.appendChild(wrapper);
    };

    const setActiveYearButton = (selectedYear)=>{
      if(!yearList) return; Array.from(yearList.querySelectorAll('button[data-year]')).forEach(btn=>{ const isActive = Number(btn.dataset.year)===selectedYear; btn.className = isActive ? 'year-btn active' : 'year-btn'; }); };

    if(yearList){ years.forEach(year=>{ const btn=document.createElement('button'); btn.type='button'; btn.dataset.year=String(year); btn.textContent=String(year); btn.className='year-btn'; btn.addEventListener('click', ()=>{ renderYear(year); setActiveYearButton(year); }); yearList.appendChild(btn); }); }
    renderYear(years[0]); setActiveYearButton(years[0]);
  }

  // toggles for problems/solutions
  const solItems = Array.from(document.querySelectorAll('.profile-solution-item'));
  const solBtn = document.getElementById('toggle-solutions-btn');
  if(solBtn && solItems.length>7){ let expanded=false; const apply=()=>{ solItems.forEach((it,idx)=>{ if(!expanded && idx>=7) it.classList.add('hidden'); else it.classList.remove('hidden'); }); solBtn.textContent = expanded ? 'Show less' : 'View all solutions'; }; solBtn.addEventListener('click', ()=>{ expanded=!expanded; apply();}); apply(); }

  const probItems = Array.from(document.querySelectorAll('.profile-problem-item'));
  const probBtn = document.getElementById('toggle-problems-btn');
  if(probBtn && probItems.length>7){ let expanded=false; const apply=()=>{ probItems.forEach((it,idx)=>{ if(!expanded && idx>=7) it.classList.add('hidden'); else it.classList.remove('hidden'); }); probBtn.textContent = expanded ? 'Show less' : 'View all problems'; }; probBtn.addEventListener('click', ()=>{ expanded=!expanded; apply();}); apply(); }
})();

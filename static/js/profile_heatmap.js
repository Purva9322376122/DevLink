function initGitHubHeatmap() {
  const container = document.getElementById('contrib-heatmap');
  if (!container) return;

  const YEAR = parseInt(container.dataset.year || new Date().getFullYear(), 10);
  const rawContributions = window.CONTRIBUTIONS_RAW || {};

  // Exact LeetCode / GitHub intensity palette
  const palette = ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'];

  function formatDateYMD(d) {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  const yearStart = new Date(YEAR, 0, 1);
  yearStart.setHours(0, 0, 0, 0);

  const yearEnd = new Date(YEAR, 11, 31);
  yearEnd.setHours(23, 59, 59, 999);

  // Find Sunday on or before Jan 1 of YEAR
  const startDate = new Date(yearStart);
  startDate.setDate(startDate.getDate() - startDate.getDay());
  startDate.setHours(0, 0, 0, 0);

  // Statistics calculation: Active Days, Current Streak, Max Streak
  let activeDays = 0;
  let currentStreak = 0;
  let maxStreak = 0;
  let tempStreak = 0;

  const yearCounts = {};
  for (let d = new Date(yearStart); d <= yearEnd; d.setDate(d.getDate() + 1)) {
    const ymd = formatDateYMD(d);
    const cnt = parseInt(rawContributions[ymd] || 0, 10);
    yearCounts[ymd] = cnt;
    if (cnt > 0) {
      activeDays++;
      tempStreak++;
      if (tempStreak > maxStreak) maxStreak = tempStreak;
    } else {
      tempStreak = 0;
    }
  }

  const today = new Date();
  const checkDate = today < yearEnd ? new Date(today) : new Date(yearEnd);
  checkDate.setHours(0, 0, 0, 0);

  while (checkDate >= yearStart) {
    const ymd = formatDateYMD(checkDate);
    if ((yearCounts[ymd] || 0) > 0) {
      currentStreak++;
      checkDate.setDate(checkDate.getDate() - 1);
    } else {
      break;
    }
  }

  // Update Header Stats
  const activeDaysEl = document.getElementById('stat-active-days');
  const currentStreakEl = document.getElementById('stat-current-streak');
  const maxStreakEl = document.getElementById('stat-max-streak');

  if (activeDaysEl) activeDaysEl.textContent = activeDays;
  if (currentStreakEl) currentStreakEl.textContent = currentStreak;
  if (maxStreakEl) maxStreakEl.textContent = maxStreak;

  // Calculate week X positions with proper month spacing gaps
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const weekMonthAssignment = [];

  for (let w = 0; w < 53; w++) {
    const midWeek = new Date(startDate);
    midWeek.setDate(startDate.getDate() + w * 7 + 3);
    let m = midWeek.getMonth();
    if (midWeek < yearStart) m = 0;
    if (midWeek > yearEnd) m = 11;
    weekMonthAssignment.push(m);
  }

  const MONTH_GAP = 12; // Gap in pixels between different months
  const weekXPositions = [];
  const monthLabelXPositions = {};

  let currentX = 0;
  let lastMonth = -1;

  for (let w = 0; w < 53; w++) {
    const m = weekMonthAssignment[w];
    if (lastMonth !== -1 && m !== lastMonth) {
      currentX += MONTH_GAP; // Add distinct month spacing gap
    }
    if (monthLabelXPositions[m] === undefined) {
      monthLabelXPositions[m] = currentX;
    }
    weekXPositions.push(currentX);
    currentX += 13; // 11px square + 2px gap
    lastMonth = m;
  }

  const totalWidth = currentX;

  // Build LeetCode Style SVG Calendar with proper month spacing gaps
  const svgNS = 'http://www.w3.org/2000/svg';
  container.innerHTML = '';

  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('class', 'contrib-svg-graph');
  svg.setAttribute('viewBox', `0 0 ${totalWidth} 115`);
  svg.style.width = '100%';
  svg.style.height = 'auto';

  // 1. Render Heatmap Rectangles (53 weeks x 7 days)
  for (let w = 0; w < 53; w++) {
    const xPos = weekXPositions[w];
    for (let dow = 0; dow < 7; dow++) {
      const cellDate = new Date(startDate);
      cellDate.setDate(startDate.getDate() + w * 7 + dow);

      const ymd = formatDateYMD(cellDate);
      const rect = document.createElementNS(svgNS, 'rect');
      const yPos = dow * 13;

      rect.setAttribute('x', xPos.toString());
      rect.setAttribute('y', yPos.toString());
      rect.setAttribute('width', '11');
      rect.setAttribute('height', '11');
      rect.setAttribute('rx', '2');
      rect.setAttribute('ry', '2');
      rect.setAttribute('class', 'contrib-svg-rect');
      rect.setAttribute('data-date', ymd);

      if (cellDate < yearStart || cellDate > yearEnd) {
        rect.setAttribute('fill', palette[0]);
        rect.setAttribute('opacity', '0.3');
      } else {
        const count = parseInt(rawContributions[ymd] || 0, 10);
        let colorIdx = 0;
        if (count >= 4) colorIdx = 4;
        else if (count === 3) colorIdx = 3;
        else if (count === 2) colorIdx = 2;
        else if (count === 1) colorIdx = 1;

        rect.setAttribute('fill', palette[colorIdx]);
        rect.setAttribute('data-count', count.toString());

        rect.addEventListener('mouseenter', e => showTooltip(e.currentTarget));
        rect.addEventListener('mouseleave', hideTooltip);
      }

      svg.appendChild(rect);
    }
  }

  // 2. Render Month Labels at BOTTOM aligned with each month block
  monthNames.forEach((mName, mIdx) => {
    const xPos = monthLabelXPositions[mIdx];
    if (xPos !== undefined) {
      const text = document.createElementNS(svgNS, 'text');
      text.setAttribute('x', xPos.toString());
      text.setAttribute('y', '108');
      text.setAttribute('class', 'contrib-svg-month');
      text.textContent = mName;
      svg.appendChild(text);
    }
  });

  container.appendChild(svg);

  // Global Tooltip
  let tip = document.getElementById('heatmap-tooltip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'heatmap-tooltip';
    tip.className = 'heatmap-tip';
    tip.style.display = 'none';
    document.body.appendChild(tip);
  }

  function showTooltip(target) {
    const date = target.getAttribute('data-date');
    const count = target.getAttribute('data-count') || 0;
    tip.innerText = `${count} contribution${count == 1 ? '' : 's'} on ${date}`;
    tip.style.display = 'block';
    const rect = target.getBoundingClientRect();
    tip.style.left = (rect.left + window.scrollX + rect.width / 2 - tip.offsetWidth / 2) + 'px';
    tip.style.top = (rect.top + window.scrollY - tip.offsetHeight - 8) + 'px';
  }

  function hideTooltip() {
    tip.style.display = 'none';
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGitHubHeatmap);
} else {
  initGitHubHeatmap();
}

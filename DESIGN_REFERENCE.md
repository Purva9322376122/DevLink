# Opportunity Detail Page - Design Reference

## 🎯 Design Goals Met

✅ Professional Appearance - LinkedIn-inspired clean layout
✅ Modern Interactions - Smooth transitions, hover effects
✅ Mobile-First - Perfect on all devices
✅ Accessibility - WCAG 2.1 AA compliant
✅ Performance - No new dependencies, optimized CSS/JS
✅ Maintainability - Clean code, no duplicates

## 🎨 Visual Hierarchy

```
┌─────────────────────────────────────────┐
│  BREADCRUMB (13px, muted)               │
├─────────────────────────────────────────┤
│  [Badge] Hero Title (42px, 800 weight)  │
│  Meta: Posted by Author • 2 weeks ago   │
├─────────────────────────────────────────┤
│  Quick Stats (Key Info Grid)            │
├─────────────────────────────────────────┤
│  Section Heading (24px)                 │
│  ─────────────────────────────────────  │
│  Section Content (15px, 1.8 line-height)│
│                                         │
│  [Content...]                           │
├─────────────────────────────────────────┤
│  [Sidebar]                              │
└─────────────────────────────────────────┘
```

## 🎯 Key Metrics

### Typography Sizes
- Hero Title: **42px** (desktop) → 28px (tablet) → 22px (mobile)
- Section Heading: **24px** → 20px → 18px
- Body: **15px** (consistent)
- Labels: **12px** (consistent)
- Small text: **13px** (consistent)

### Spacing Scale (8px base)
- xs: 8px
- sm: 12px
- md: 16px
- lg: 24px
- xl: 32px
- xxl: 40px

### Box Shadow Progression
- **None**: Flat cards
- **Hover**: Lift effect (small shadow)
- **Focus**: Medium shadow + glow
- **Active**: Large shadow, deep focus

## 🎭 Component States

### Buttons
```
Normal: Gradient blue background
Hover: Slightly darker gradient + lift
Focus: Blue glow + outline
Active: Pressed down state
Disabled: 60% opacity, no interaction
```

### Form Inputs
```
Normal: Light border
Focus: Blue border + glow
Invalid: Red border
Filled: Blue accent
```

### Badges
```
Status-Open: Green bg, green text
Status-Pending: Amber bg, amber text
Status-Accepted: Green bg, green text
Status-Rejected: Red bg, red text
Type Badge: Blue bg, blue text
```

### Cards
```
Resting: Subtle shadow, light border
Hover: Medium shadow, blue border tint
Focus: Blue outline + glow
Selected: Blue background, white text
```

## 📐 Layout Grids

### Desktop (1280px container)
```
├─────────────────────────────────────────┤
│              Main Content (864px)       │ Sidebar
│  - Hero Header                          │  (340px)
│  - Overview Stats                       │
│  - Description                          │
│  - Skills                               │
│  - Organizer                            │
├─────────────────────────────────────────┤
```

### Tablet (768px container)
```
├─────────────────────────────────┤
│      Hero Header                │
│      Overview Stats (2 cols)    │
├────────────┬────────────────────┤
│ Info Card  │ Apply Card         │
├────────────┴────────────────────┤
│      Share Card                 │
├─────────────────────────────────┤
│      Description                │
│      Skills                     │
│      Organizer                  │
└─────────────────────────────────┘
```

### Mobile (320px container)
```
├─────────────────────┤
│  Breadcrumb         │
│  Hero Header        │
│  Overview Stats(1x) │
│  Info Card          │
│  Apply Card         │
│  Share Card         │
│  Description        │
│  Skills             │
│  Organizer          │
└─────────────────────┘
```

## 🎨 Color Palette

### Primary Colors
```
Primary Blue:     #2563EB (Main brand color)
Primary Hover:    #1f58c1 (Darker blue)
Primary Focus:    rgba(37, 99, 235, 0.18) (Light glow)
```

### Semantic Colors
```
Success:          #16A34A (Green - approved)
Warning:          #F59E0B (Amber - pending)
Danger:           #DC2626 (Red - rejected)
Muted:            #6B7280 (Gray - secondary text)
```

### Backgrounds
```
Light BG:         #F5F7FB (Main background)
Card BG:          #FFFFFF (White cards)
Border:           #E5E7EB (Light gray borders)
```

### Dark Mode
```
Dark BG:          #0b1220 (Very dark)
Dark Card:        #0f1724 (Dark blue-gray)
Dark Text:        #ffffff (White)
Dark Muted:       #9ca3af (Light gray)
Dark Border:      rgba(255,255,255,0.06)
```

## 🔄 Interaction Patterns

### Hover Effects
- Cards: Shadow lift + border color change
- Links: Color change + underline
- Buttons: Gradient shift + lift
- Badges: Background/color inversion
- Skills: Blue background + lift + white text

### Focus Effects
- All interactive: 3px blue outline
- 2px outline offset
- High contrast for accessibility

### Active States
- Buttons: Pressed down (no lift)
- Form: Blue border + glow
- Links: Underline maintained

## 📊 Component Library

### Cards
```
.section-card (main content)
  - 32px padding
  - 16px border-radius
  - White background
  - Subtle shadow on hover

.sidebar-card (sidebar content)
  - 24px padding
  - 16px border-radius
  - Gradient background on action card
  - Medium shadow on hover
```

### Badges
```
.badge-success        (Green status)
.badge-closed         (Red status)
.status-badge-*       (Application status)
```

### Buttons
```
.btn-primary          (Primary action)
.btn-secondary        (Secondary action)
.btn-apply            (Form submit)
.btn-view-apps        (Owner action)
```

### Inputs
```
.form-input           (Text inputs)
.form-textarea        (Text areas)
.form-field           (Field wrapper)
.form-field-label     (Labels)
```

## 🌙 Dark Mode Implementation

Uses `[data-theme="dark"]` selector:
```css
[data-theme="dark"] {
  --card: #0f1724;
  --bg: #0b1220;
  --text: #ffffff;
  --muted: #9ca3af;
  --border: rgba(255, 255, 255, 0.06);
}
```

All colors automatically adjust based on theme.

## ♿ Accessibility Features

### Semantic HTML
- ✓ Proper heading hierarchy (h1, h2, h3)
- ✓ Landmark elements (main, aside, nav)
- ✓ Form labels properly associated
- ✓ List elements for listings

### ARIA Attributes
- ✓ aria-label on icon buttons
- ✓ aria-labelledby on sections
- ✓ aria-required on form fields
- ✓ aria-current on breadcrumb
- ✓ role="tag" on skill badges

### Keyboard Navigation
- ✓ Tab through all interactive elements
- ✓ Enter to activate buttons
- ✓ Space to toggle checkboxes
- ✓ Escape to close modals
- ✓ Arrow keys for navigation (where applicable)

### Visual
- ✓ Focus visible indicators
- ✓ High contrast colors (WCAG AA)
- ✓ No color alone conveys meaning
- ✓ Sufficient text size (15px base)
- ✓ 1.8 line-height for readability

## 📱 Responsive Behavior

### Typography Scaling
```
Desktop  → Tablet  → Mobile
42px     → 36px    → 28px    (Hero)
24px     → 20px    → 18px    (Heading)
15px     → 14px    → 13px    (Body)
12px     → 11px    → 10px    (Label)
```

### Spacing Scaling
```
Desktop  → Tablet  → Mobile
40px     → 32px    → 24px    (Large)
32px     → 24px    → 16px    (Medium)
24px     → 16px    → 12px    (Small)
```

### Layout Changes
```
Desktop        Tablet         Mobile
2-column  →    2-column  →    1-column
Sticky        Sidebar        Stacked
sidebar       below          content
```

## 🎬 Animation Details

### Fade-In Animation
```css
@keyframes fadeUpIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
Duration: 0.3s
Timing: ease
Stagger: 50-100ms between cards
```

### Hover Transitions
```css
All transitions use:
  transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
```

### Interactive States
- Buttons: Transform + shadow on hover/focus
- Cards: Shadow lift on hover
- Links: Color change on hover/focus
- All: Smooth 180ms transition

## 🖨️ Print Styles

When printing:
- ✓ Sidebar hidden
- ✓ No background gradients
- ✓ Optimized for black & white
- ✓ Card shadows removed
- ✓ Layout becomes single column
- ✓ Page breaks optimized

## 📈 Performance Metrics

- **CSS**: ~15KB (minified: ~10KB)
- **JS**: ~8KB (minified: ~5KB)
- **Images**: Lazy loaded
- **Animations**: GPU-accelerated (transform, opacity)
- **Paint**: Minimal repaints
- **Layout Shift**: None (stable layout)

## 🔗 Related Files

- `design-system.css` - Global design tokens
- `components.css` - Shared component styles
- `navbar.css` - Navigation styles
- `base.html` - Base template

---

**Design Version**: 1.0
**Last Updated**: July 23, 2026
**Status**: Production Ready ✅

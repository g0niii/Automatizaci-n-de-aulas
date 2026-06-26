# Design System: IMSCC Maquetador UCC
**Version 1.0** | Professional Course Layout Automation Dashboard

---

## 1. Brand & Identity

### Color Palette
| Role | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Primary Brand** | `#1b1e31` | 27, 30, 49 | Navbar, buttons, accents (UCC corporate color) |
| **Primary Light** | `#2a2d47` | 42, 45, 71 | Hover states, secondary buttons |
| **Accent (Success)** | `#22C55E` | 34, 197, 94 | Confidence badges ≥80%, success states |
| **Warning** | `#F59E0B` | 245, 158, 11 | Confidence badges 60-79%, warnings |
| **Danger/Error** | `#EF4444` | 239, 68, 68 | Bloqueantes (red badges), error states |
| **Neutral Gray** | `#6B7280` | 107, 114, 128 | Secondary text, borders, muted elements |
| **Light Gray** | `#F3F4F6` | 243, 244, 246 | Backgrounds, cards, subtle containers |
| **White** | `#FFFFFF` | 255, 255, 255 | Primary backgrounds, card fills |
| **Dark Gray** | `#111827` | 17, 24, 39 | Body text, primary text (light mode) |

### Typography
| Element | Font | Weight | Size | Line Height |
|---------|------|--------|------|-------------|
| **Headings (H1-H2)** | Poppins | 600-700 | 28-36px | 1.2 |
| **Headings (H3-H4)** | Poppins | 600 | 20-24px | 1.3 |
| **Body Text** | Open Sans | 400-500 | 14-16px | 1.5-1.6 |
| **Labels/Inputs** | Open Sans | 500 | 14px | 1.4 |
| **Badges/Tags** | Open Sans | 600 | 12px | 1.4 |
| **Monospace (Code)** | JetBrains Mono | 400 | 12-13px | 1.5 |

**Google Fonts Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Open+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```

---

## 2. Component Patterns

### Wizard Flow Layout
**Architecture:** 4-step linear wizard with progress indicator

```
┌─────────────────────────────────────────────────────────────┐
│ IMSCC Maquetador UCC                            [? Help] [👤] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Step 1: Upload          Step 2: Plan        Step 3: Edit   │
│  ✓ Upload ZIP     ───>   ✓ Review Plan  ──>  ☐ Validar     │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                      [STEP CONTENT]                           │
│                                                               │
│                  [Cancel]  [Previous]  [Next/Generate]       │
└─────────────────────────────────────────────────────────────┘
```

### Color Semantics for Course Items
- **Green (#22C55E)** - Confidence ≥80%: High confidence matches
- **Yellow (#F59E0B)** - Confidence 60-79%: Probable matches, needs review
- **Red (#EF4444)** - Bloqueante (confidence <60% or critical issue): Prevents generation
- **Gray (#6B7280)** - INFO: Informational issues, doesn't block

### Badge System
```
[✓ 95%]  - Green badge, high confidence
[⚠ 72%]  - Yellow badge, needs review
[✗ Bloqueante]  - Red badge, blocks generation
[ℹ Info]  - Gray badge, FYI only
```

---

## 3. Page Templates

### Step 1: File Upload
**Purpose:** Accept ZIP of course folder

**Layout:**
```
[Título] Upload Course Material
[Descripción] Select your course folder (ZIP)

┌─────────────────────────────────────────────────┐
│ 📁 Drag and drop or click to upload             │
│                                                 │
│    Supported: ZIP files (max 500MB)             │
│    Structure: Programa, Desarrollo, Diseño, ... │
└─────────────────────────────────────────────────┘

[Recent uploads]
- Conti_Avanzado_2026.zip   [6 days ago]  [Re-upload]
- Agile_PM_2026.zip         [3 days ago]  [Re-upload]
```

**State Machine:**
- Idle → User hovers drop zone (border highlight: #1b1e31)
- Idle → User selects file (spinner, "Processing...")
- Loading → Parse ZIP, scan folders → Show Step 2 (auto-advance)
- Error → Red error banner with retry button

### Step 2: Plan Review
**Purpose:** Visualize course structure with confidence metrics

**Layout (Table/Expandable):**
```
┌────────────────────────────────────────────────────────────────────┐
│ Course: Ética y Cumplimiento | Module: 1 (Introducción)           │
├────────────────────────────────────────────────────────────────────┤
│ Item                           │ Confidence │ Source    │ Issues   │
├────────────────────────────────┼────────────┼───────────┼──────────┤
│ 1.1 Introducción al Módulo     │ [✓ 95%]   │ DOCX      │ —        │
│ 1.2 Lectura Obligatoria        │ [⚠ 72%]   │ XLSX      │ [ℹ INFO] │
│ 1.3 Video Tutorial             │ [✓ 88%]   │ DOCX      │ —        │
│ Foro Obligatorio M1            │ [✗ 45%]   │ (Missing) │ [!]      │
│ Actividad Obligatoria M1       │ [✓ 92%]   │ XLSX      │ —        │
└────────────────────────────────┴────────────┴───────────┴──────────┘

[Theme selector] Education / Posgrado

[Issues & Warnings]
⚠ 1 bloqueante (red items) — Cannot generate until resolved
ℹ 3 info items — Review before generating
✓ 8/9 items ready
```

**Click item to expand:**
```
Item: 1.2 Lectura Obligatoria [⚠ 72%]

Source XLSX:
  Page Title: Lectura Obligatoria - Semana 1
  Link: https://drive.google.com/...

Source DOCX:
  (no match found)

Confidence: 72%
Reason: Title match high, but no content in DOCX

[Edit Source] [Mark as reviewed]
```

### Step 3: Plan Editor
**Purpose:** Adjust confidence/sources before generation

**UI Elements:**
- **Editable table rows** (for advanced users)
- **Quick-fix buttons:**
  - "Mark reviewed" (removes yellow badges)
  - "Force source: XLSX/DOCX/Both"
  - "Skip this item"
  - "Use as-is"
- **Validation:** Real-time check for bloqueantes

**State after edits:**
```
✓ All items reviewed
✓ 0 bloqueantes
✓ Ready to generate

[Generate IMSCC]  ← Button enabled
```

### Step 4: Generate & Download
**Purpose:** Generate .imscc and provide download

**UI:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Generating... [████████████░░░░░░░░░] 68%                       │
│                                                                   │
│ ✓ Parsing course structure                                       │
│ ✓ Extracting content from DOCX                                   │
│ ✓ Building pages with snippets                                   │
│ → Packaging IMSCC... (in progress)                               │
└─────────────────────────────────────────────────────────────────┘

When complete:
[✓ Success]
  File ready: Etica_Cumplimiento_2026.imscc (42 MB)
  Generated: 2026-06-21 14:32:15
  
  [Download] [View Details] [Generate Another]
```

**Error states:**
```
[✗ Generation failed]
  Error: Bloqueante found during validation
  Details: Foro Obligatorio M1 not found in DOCX
  
  [← Back to edit] [View full log]
```

---

## 4. Interaction Patterns

### Hover States
- **Buttons:** 150-200ms color/shadow transition
  - Normal: `#1b1e31`
  - Hover: `#2a2d47` (darker)
  - Focus: `outline: 3px solid #1b1e31` (keyboard nav)
  
- **Table rows:** Subtle background highlight `#F3F4F6`
  
- **Badge/tags:** No scale shift (prevent layout jump); opacity 0.8→1.0

### Loading States
- **Spinner:** 300ms rotations, centered in container
- **Skeleton screens:** Light gray (#F3F4F6) with animated pulse
- **Button feedback:** Disable, show spinner inside, "Processing..."

### Success/Error Feedback
- **Success:** Green (#22C55E) checkmark + toast message (3s auto-dismiss)
- **Error:** Red (#EF4444) alert + explanation + retry button
- **Info:** Gray (#6B7280) badge or small notification

### Form Validation
- **On blur:** Validate field, show error inline
- **Errors:** Red text below field (left-aligned)
- **Success:** Green checkmark or subtle green border
- **ARIA labels:** `aria-label`, `aria-describedby` on inputs

---

## 5. Responsive Design

### Breakpoints
| Device | Width | Layout |
|--------|-------|--------|
| Mobile | 375px | Single column, stacked |
| Tablet | 768px | 2-column grid where possible |
| Desktop | 1024px+ | 3+ columns, full layout |

### Mobile Adjustments
- **Font sizes:** Minimum 16px on inputs (iOS zoom prevention)
- **Touch targets:** 44x44px minimum
- **Upload area:** Full-width, taller for touch
- **Table:** Horizontal scroll on small screens OR collapse to cards
- **Buttons:** Full-width on mobile, stacked vertically

---

## 6. Dark Mode Support

### Dark Palette
| Element | Light | Dark |
|---------|-------|------|
| Background | #FFFFFF | #111827 |
| Card | #FFFFFF | #1F2937 |
| Text | #111827 | #F3F4F6 |
| Border | #E5E7EB | #4B5563 |
| Accent | #1b1e31 | #60A5FA (lighter for contrast) |

**Implementation:**
```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #111827;
    --bg-card: #1F2937;
    --text-primary: #F3F4F6;
    --border: #4B5563;
  }
}
```

**No auto dark mode for Step 1 Upload** (keep light to match web standard).

---

## 7. Accessibility (WCAG AA)

### Color Contrast
- Text on backgrounds: 4.5:1 minimum
- Verified pairs:
  - Dark gray (#111827) on white: ✓ 16:1
  - Dark gray (#111827) on light gray: ✓ 10.8:1
  - White on brand (#1b1e31): ✓ 8.2:1
  - Green badge (#22C55E) text: Dark gray only (not white)

### Keyboard Navigation
- Tab order: Left-to-right, top-to-bottom
- Focus visible: 3px solid outline in brand color
- Skip to content link on load

### Form Accessibility
- Every input has `<label for="id">`
- Error messages tied with `aria-describedby`
- Required fields marked with `aria-required="true"`

### Images & Icons
- All meaningful images: descriptive alt text
- Icons in buttons: `aria-label` (e.g., `aria-label="Upload file"`)
- Decorative icons/dividers: `aria-hidden="true"`

### Motion
- Respect `prefers-reduced-motion`: disable animations/transitions if set
- No autoplaying videos or infinite loops

---

## 8. Performance & Loading

### Optimization Targets
- **First Contentful Paint:** < 1.5s
- **Largest Contentful Paint:** < 2.5s
- **Cumulative Layout Shift:** < 0.1
- **Time to Interactive:** < 3.5s

### Image Strategy
- **Formats:** WebP with JPEG fallback
- **Sizes:** Responsive srcset
- **Lazy loading:** `loading="lazy"` on below-fold images

### Code Splitting (React/Vite)
- Upload step: Lazy-load file parser (async import)
- Plan editor: Lazy-load table/form components
- Generate: Load after user confirms (no preload)

---

## 9. React Component Architecture

### Folder Structure
```
src/
├── pages/
│   ├── Wizard.tsx          # Main 4-step container
│   ├── Step1Upload.tsx
│   ├── Step2PlanReview.tsx
│   ├── Step3PlanEditor.tsx
│   └── Step4Generate.tsx
├── components/
│   ├── ProgressBar.tsx     # Wizard progress indicator
│   ├── ConfidenceBadge.tsx
│   ├── IssueMarker.tsx
│   ├── UploadArea.tsx
│   ├── PlanTable.tsx
│   ├── ThemeSelector.tsx
│   └── LoadingSpinner.tsx
├── hooks/
│   ├── useCourseUpload.ts
│   ├── usePlanEditor.ts
│   └── useValidation.ts
├── types/
│   └── course.ts           # Interfaces (CourseSpec, etc.)
├── utils/
│   ├── api.ts              # Fetch calls to Flask backend
│   ├── validation.ts
│   └── format.ts           # Formatting helpers
└── styles/
    └── tailwind.css        # Tailwind + custom vars
```

### Key Hooks
- **`useCourseUpload`:** Handle ZIP upload, parse, call backend
- **`usePlanEditor`:** Manage plan state, edits, validation
- **`useValidation`:** Real-time validation, confidence calculation

### Context (if needed)
```tsx
<CourseProvider>
  <Wizard />
</CourseProvider>
```

---

## 10. Styling Strategy

### Tailwind CSS Configuration
```js
module.exports = {
  theme: {
    colors: {
      'brand': '#1b1e31',
      'brand-light': '#2a2d47',
      'success': '#22C55E',
      'warning': '#F59E0B',
      'danger': '#EF4444',
      'neutral': '#6B7280',
      'light': '#F3F4F6',
      // Standard Tailwind colors for white, gray, etc.
    },
    fontFamily: {
      'sans': ['Open Sans', 'sans-serif'],
      'heading': ['Poppins', 'sans-serif'],
      'mono': ['JetBrains Mono', 'monospace'],
    },
  },
};
```

### Class Naming Convention
```tsx
// Component:
<div className="wizard-container max-w-6xl mx-auto p-6">
  <header className="wizard-header bg-brand text-white">
    <h1 className="font-heading text-2xl font-bold">
      IMSCC Maquetador UCC
    </h1>
  </header>
  
  <main className="wizard-content bg-light">
    <div className="step-1 grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* content */}
    </div>
  </main>
  
  <footer className="wizard-footer flex justify-end gap-3 p-6">
    <button className="btn btn-secondary">Cancel</button>
    <button className="btn btn-primary">Next</button>
  </footer>
</div>
```

### Button Variants
```tsx
// Primary (brand color)
<button className="btn-primary bg-brand hover:bg-brand-light text-white px-6 py-2 rounded-lg transition-colors duration-200">
  Generate
</button>

// Secondary (light)
<button className="btn-secondary border border-neutral text-neutral hover:bg-light px-6 py-2 rounded-lg transition-colors duration-200">
  Cancel
</button>

// Disabled
<button disabled className="btn-primary opacity-50 cursor-not-allowed">
  Generate
</button>
```

---

## 11. Implementation Checklist

### Phase 1: Setup
- [ ] Install Vite + React + TypeScript
- [ ] Configure Tailwind CSS
- [ ] Add Google Fonts import
- [ ] Set up folder structure
- [ ] Create type definitions (CourseSpec)

### Phase 2: Components
- [ ] Build ProgressBar (Step 1/2/3/4 indicator)
- [ ] Build UploadArea (drag-drop, file input)
- [ ] Build ConfidenceBadge (green/yellow/red badges)
- [ ] Build PlanTable (expandable rows, editable fields)
- [ ] Build ThemeSelector (Educación/Posgrado radio buttons)
- [ ] Build LoadingSpinner (animated SVG)

### Phase 3: Pages
- [ ] Step 1: Upload → parse → call `/api/plan` (backend)
- [ ] Step 2: PlanReview → show plan + issues
- [ ] Step 3: PlanEditor → editable table + validations
- [ ] Step 4: Generate → call `/api/generate` → download

### Phase 4: Integration
- [ ] Connect to Flask backend API routes
- [ ] Error handling + toasts
- [ ] Loading states + spinners
- [ ] Success feedback + downloads
- [ ] Form validation + ARIA labels

### Phase 5: Polish
- [ ] Responsive testing (375/768/1024/1440px)
- [ ] Dark mode toggle
- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Accessibility audit (WCAG AA)
- [ ] Performance optimization (lazy load, code split)
- [ ] Browser testing (Chrome, Firefox, Safari, Edge)

### Phase 6: QA
- [ ] Test wizard flow end-to-end
- [ ] Test error states
- [ ] Test file upload (large files, edge cases)
- [ ] Test on mobile devices
- [ ] Verify dark mode contrast

---

## 12. Anti-Patterns to Avoid

❌ **Do NOT:**
- Use emoji as UI icons (🎨, 🚀) — use SVG icons from Heroicons/Lucide
- Auto-advance between steps without user confirmation
- Auto-scale buttons/cards on hover (causes layout shift)
- Use placeholder-only inputs without `<label>` tags
- Show 0 feedback on file upload (spinner mandatory)
- Allow generation with bloqueantes (disable button)
- Use gradients or heavy shadows (keep it minimal)
- Mix multiple font families (only Poppins + Open Sans)
- Validate only on submit (validate on blur)

✅ **DO:**
- Use SVG icons consistently (all same size: 24x24 or 20x20)
- Add `cursor-pointer` to all interactive elements
- Use `transition-colors duration-200` on hovers
- Provide `aria-label` on icon-only buttons
- Always show spinner + status text during async work
- Disable submit button during request
- Keep spacing mathematical (8px grid)
- Use semantic HTML (`<form>`, `<button>`, `<label>`)
- Validate on blur, show inline errors
- Test keyboard navigation (Tab, arrow keys, Enter)

---

## 13. Next Steps

1. **Approve design system** — Feedback on colors, typography, layout?
2. **Start React setup** — Vite, Tailwind, component structure
3. **Build components incrementally** — Test each in Storybook/React docs
4. **Connect to Flask backend** — API routes for `/plan` and `/generate`
5. **Test end-to-end** — Upload ZIP → Plan → Edit → Generate → Download
6. **Deploy & iterate** — User feedback on UX refinements

---

**Design by:** UI/UX Pro Max  
**Date:** 2026-06-21  
**Project:** IMSCC Maquetador UCC  
**Stack:** React 18 + Vite + TypeScript + Tailwind CSS  
**Target:** Professional Course Layout Automation Dashboard

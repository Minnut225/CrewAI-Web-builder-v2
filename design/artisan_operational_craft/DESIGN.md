---
name: Artisan Operational Craft
colors:
  surface: '#fff8f5'
  surface-dim: '#e9d7cb'
  surface-bright: '#fff8f5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fff1e9'
  surface-container: '#fdeadf'
  surface-container-high: '#f7e5d9'
  surface-container-highest: '#f1dfd4'
  on-surface: '#231a13'
  on-surface-variant: '#50443f'
  inverse-surface: '#392e27'
  inverse-on-surface: '#ffede3'
  outline: '#82746f'
  outline-variant: '#d4c3bc'
  surface-tint: '#765849'
  primary: '#220f05'
  on-primary: '#ffffff'
  primary-container: '#3a2317'
  on-primary-container: '#ab8878'
  inverse-primary: '#e5beac'
  secondary: '#88512a'
  on-secondary: '#ffffff'
  secondary-container: '#fdb385'
  on-secondary-container: '#78431e'
  tertiary: '#001907'
  on-tertiary: '#ffffff'
  tertiary-container: '#003013'
  on-tertiary-container: '#5c9e6a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbcb'
  primary-fixed-dim: '#e5beac'
  on-primary-fixed: '#2b160b'
  on-primary-fixed-variant: '#5c4133'
  secondary-fixed: '#ffdbc7'
  secondary-fixed-dim: '#ffb689'
  on-secondary-fixed: '#311300'
  on-secondary-fixed-variant: '#6c3a15'
  tertiary-fixed: '#adf3b8'
  tertiary-fixed-dim: '#92d69d'
  on-tertiary-fixed: '#00210b'
  on-tertiary-fixed-variant: '#0a5226'
  background: '#fff8f5'
  on-background: '#231a13'
  surface-variant: '#f1dfd4'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 22px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  currency-display:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: 0.01em
  currency-cell:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  hotkey-kbd:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-base: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
---

## Brand & Style

This design system is tailored for high-velocity coffee shop operations, balancing operational clarity at the counter (POS, KDS) with analytical depth for back-office management (inventory, staff, accounting). The aesthetic blends **Modern SaaS Precision** with an **Artisan Warmth** philosophy. It strips away digital harshness through organic undertones while maintaining the structural discipline, density, and legibility required for high-throughput touch and desktop interactions.

### Personality & Values
- **Warm Authority:** Robust, grounded tones reminiscent of dark roast espresso and raw linen replace generic cold tech grays.
- **Ergonomic Speed:** High visual affordance, rapid-scan typography, and tactile contrast designed for fast order entry and low-error table management.
- **Quiet Utility:** Interfaces recede into the physical cafe environment rather than glowing invasively, preventing screen fatigue during extended 8-to-12-hour shifts.

### Visual Style
- **Warm Minimalist Tactility:** Structured container layouts with precise 1px micro-borders, organic warm-cream surfaces, and warm umber shadows instead of artificial cool blurs.

## Colors

The palette draws directly from the barista workflow: dark espresso bases, steamed milk creams, polished brass fixtures, and natural ceramic whites.

### Hierarchy & Application
- **Primary (`#3A2317`):** Deep roast espresso. Used for primary navigation, high-emphasis action triggers, header bars, and active system states.
- **Secondary (`#A0643C`):** Warm amber crema. Applied to interactive highlights, secondary confirmations, category selections, and focus indicators.
- **Backgrounds:** `#FDFBF7` serves as the primary canvas baseline; `#F7F3EB` provides recessed counter surface areas, table layout floor plans, and sidebar navigation foundations.
- **Surfaces & Cards:** Pure `#FFFFFF` elevates data cards above warm backgrounds, encased by `#E8E1D5` to maintain optical boundary integrity under varying counter lighting conditions.
- **Typography:** Primary text is pinned to `#1F140E` (Espresso Dark) to maximize WCAG AAA contrast against cream grounds; secondary descriptors utilize `#6B5E55`, and muted metadata sits at `#8C7F77`.

### Semantic Indicators
- **Success (`#2E6F40`, surface `#EAF5ED`):** Order completed, paid, stock replenished.
- **Warning (`#B4690E`, surface `#FEF6E9`):** Low inventory alert, pending kitchen ticket (>10m), unprinted receipt.
- **Destructive/Error (`#B92B27`, surface `#FDF0ED`):** Canceled ticket, refund initiated, out of stock.
- **Info (`#3E657D`, surface `#EDF4F8`):** Dine-in table status note, shift change notification.

## Typography

The type system prioritizes high scanning speeds in crowded environments and clear formatting for Vietnamese text and numerical currency strings (`45.000 ₫`).

- **Font Family:** `Plus Jakarta Sans` provides geometric legibility with humanist warmth, allowing crisp rendering on both standard POS resistive touch monitors and high-DPI tablets.
- **Tabular Figures:** All monetary figures, receipt totals, inventory counts, and timers must utilize `font-variant-numeric: tabular-nums` to ensure strict vertical column alignment in receipts and data tables.
- **Currency Symbols:** The Vietnamese Dong symbol (`₫`) must always align baseline-to-baseline with the trailing digit, formatted with regular space separation (`55.000 ₫`), never superscripted or condensed.
- **Keyboard Shortcuts (`hotkey-kbd`):** Fixed-width typographic containers indicate direct keyboard triggers (`F1`, `F4`, `Enter`, `Esc`), styled in uppercase bold for immediate employee recall.

## Layout & Spacing

The layout model adapts across three distinct operational environments: POS Touch Screen (Cashier/Counter), KDS (Barista/Kitchen Display), and Back-Office Management (Admin/Owner).

### Grid Structure
- **Counter POS View (Tablet/Touch Desktop):** Fixed two-pane layout with fluid scaling.
  - Left pane (Catalog & Categories): 60-65% width with responsive card grids (3-4 columns).
  - Right pane (Ticket / Active Order Slip): 35-40% width pinned side-sheet with sticky calculation footer.
- **Back-Office Management View:** 12-column responsive fluid grid with fixed 240px collapsable navigation rail. Max content width of 1440px centered for analytical clarity.
- **Kitchen Display System (KDS):** Fluid auto-fitting column deck (minimum card width: 280px) stretching across widescreen display terminals.

### Breakpoints & Adaptive Rules
- **Tablet Landscape / POS Terminal (1024px - 1280px):** Default standard touch zone. Target touch sizes maintain a minimum 44px × 44px active hit area with `space-sm` (8px) safety separation.
- **Desktop Management (1281px+):** Densified view for analytics, stock tables, and recipe cost formulas using `space-xs` and `space-sm` cell padding.
- **Mobile Handheld (Staff Order Taking, <768px):** Linear stacking with bottom sheet cart preview and pinned sticky payment CTA.

## Elevation & Depth

Visual hierarchy uses subtle warm-tinted ambient shadows and structured perimeter borders to stay distinct against bright fluorescent or sunlit cafe windows.

### Depth Mechanics
- **Base Level (Canvas):** Flat `#FDFBF7` with no elevation.
- **Level 1 (Cards, Menu Items, Table Tiles):** Flat `#FFFFFF` surface bounded by a crisp 1px solid border (`#E8E1D5`). Rest state carries an ambient drop shadow: `0 1px 3px rgba(43, 24, 16, 0.04), 0 1px 2px rgba(43, 24, 16, 0.02)`.
- **Level 2 (Active Table, Dragging Order, Hovered POS Tile):** Elevated card surface with `0 4px 12px rgba(43, 24, 16, 0.08)` and border tint shifting to `#A0643C`.
- **Level 3 (Flyouts, Modifier Drawers, Split-Bill Modals):** High-priority panels with `0 12px 32px rgba(43, 24, 16, 0.12)`, overlaid on top of a warm scrim (`rgba(31, 20, 14, 0.45)` with 2px backdrop blur).
- **Recessed Areas (Order Notes, Kitchen Prep Queues):** Built with background `#F7F3EB` and inset border `1px solid #E2D9CC`, producing tactile physical depth without high shadow overhead.

## Shapes

The design system uses a balanced corner language (`roundedness: 2`, matching 8px to 12px core radiuses) to preserve modern software clean lines while maintaining a welcoming presence.

### Shape Tokens & Radius Scale
- **Small Radii (4px - 6px):** System tags, keyboard shortcut badges (`hotkey-kbd`), table status pips, and input fields.
- **Medium Radii (8px - 10px):** Action buttons, POS drink selection tiles, category pill filters, and active tab triggers.
- **Large Radii (12px - 14px):** Main structural panels, order checkout summary cards, inventory data tables, and table-layout room dividers.
- **Full Pill (9999px):** Status badges (Paid, Pending, Preparing) and segmented filter chips.
- **Borders:** Consistent 1px solid boundary rule using `#E8E1D5` across surfaces. Avoid heavy or decorative borders.

## Components

### Buttons
- **Primary Action (Payment, Print, Submit):** Background `#3A2317`, text `#FFFFFF`, border none, border-radius 10px. Hover state warms to `#4E3020`; pressed state `#2B1810`. Min-height 48px on POS touch screens; 38px on desktop management.
- **Brand Action (Add Item, Apply Discount):** Background `#A0643C`, text `#FFFFFF`.
- **Secondary (Split Bill, Hold Order):** Background `#FFFFFF`, text `#3A2317`, border 1px solid `#E8E1D5`. Hover background `#F7F3EB`.
- **Destructive (Void Item, Cancel Table):** Background `#FDF0ED`, text `#B92B27`, border 1px solid `#F7D2CD`. Hover background `#B92B27`, hover text `#FFFFFF`.

### Menu & Product Cards (POS Grid)
- **Container:** Background `#FFFFFF`, border 1px solid `#E8E1D5`, border-radius 10px, padding 12px.
- **Layout:** Product title (`headline-sm`, 2 lines clamped), followed by large formatted price (`currency-cell`), followed by stock indicator badge.
- **Active / Selected State:** Border increases focus ring using `#A0643C` (2px solid) with light cream fill `#FAF5EF`.

### Receipt & Order Slip List
- **Row Architecture:** Vertical height 48px touch target. Left: Item count badge (`2x` in `#A0643C` bold) + Item name. Right: Calculated total (`currency-cell`).
- **Modifiers:** Nested indented list underneath in `body-sm` (`#6B5E55`, e.g., "+ 50% Đường, + Trân châu trắng").
- **Divider:** Subtle dotted border `1px dashed #E2D9CC`.

### Status Badges & Chips
- **Success (Served / Paid):** Background `#EAF5ED`, text `#2E6F40`, dot indicator `#2E6F40`.
- **Warning (Preparing / Delay):** Background `#FEF6E9`, text `#B4690E`, dot indicator `#B4690E`.
- **Destructive (Void / Unpaid):** Background `#FDF0ED`, text `#B92B27`, dot indicator `#B92B27`.
- **Info (Reserved Table):** Background `#EDF4F8`, text `#3E657D`, dot indicator `#3E657D`.
- **Styling:** Height 24px, padding 4px 10px, border-radius 9999px, font size 11px, weight 600.

### Input Fields & Search Bars
- **Container:** Background `#FFFFFF`, border 1px solid `#E8E1D5`, border-radius 8px, height 42px (36px desktop data tables).
- **Focus State:** Border color `#A0643C`, soft outer glow `0 0 0 3px rgba(160, 100, 60, 0.15)`.
- **Numeric Fields:** Right-aligned monetary inputs with embedded suffix `₫` in fixed `#8C7F77`.

### Table Layout Grid / Room Map
- **Table Node:** Rounded rect or circular container (radius 12px).
- **Available Table:** Background `#FFFFFF`, border 1.5px solid `#E8E1D5`, text `#1F140E`.
- **Occupied Table:** Background `#FAF5EF`, border 1.5px solid `#A0643C`, duration timer badge in `hotkey-kbd`.
- **Bill Requested:** Flashing amber border `#B4690E`, surface `#FEF6E9`.

### Specialized POS Fast-Keys (Hotkeys)
- Visual badge rendered within buttons: Background `#F7F3EB`, border 1px solid `#DCD3C5`, text `#3A2317`, font size 10px, font weight 700, padding 2px 5px, border-radius 4px.
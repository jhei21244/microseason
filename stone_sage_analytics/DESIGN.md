# Design System Document: The Precision Curator

## 1. Overview & Creative North Star

### Creative North Star: "The Digital Microscope"
In a world of oversized white space and "mobile-first" padding, this design system takes a contrarian stance: **The Precision Curator.** It is designed for the power user who views data as an art form. We reject the "one-size-fits-all" template look in favor of a high-density, editorial-grade interface that feels like a precision instrument—think high-end horology or architectural blueprints.

The system breaks the "standard UI" mold by using **intentional asymmetry** and **tonal depth** instead of structural lines. By leveraging a condensed typography scale and a "Light Stone" palette, we create an environment where the data is the hero, and the interface is the whisper-quiet stage. We move away from the "boxy" web by utilizing subtle overlaps and nested surface tiers that suggest professional-grade complexity without the clutter.

---

## 2. Colors: The Stone & Sage Palette

Our color strategy is grounded in organic, muted tones that reduce eye strain during prolonged data analysis.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning or containment. Traditional borders create visual "noise" that interferes with data density. Boundaries must be defined through:
1.  **Background Color Shifts:** Placing a `surface_container_low` section atop a `background` or `surface` base.
2.  **Tonal Transitions:** Using `surface_container` variants to differentiate header areas from content areas.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers of fine paper. 
- **Base Layer:** `surface` (#faf9f6)
- **Primary Layout Sections:** `surface_container_low` (#f3f4f0)
- **Interactive Cards/Tables:** `surface_container_lowest` (#ffffff) to provide a crisp, "elevated" feel without shadows.
- **Secondary Utility Panels:** `surface_container_high` (#e5e9e4) or `highest` (#dee4de) for sidebars or navigation.

### The "Glass & Gradient" Rule
To ensure the system feels premium and not just "flat," use **Glassmorphism** for floating overlays (e.g., Command Palettes, Tooltips). 
- **Token:** `surface_variant` at 70% opacity + `backdrop-blur: 12px`.
- **Signature Gradients:** For main CTAs or "Total Sum" cards, use a subtle linear gradient from `primary` (#526351) to `primary_container` (#d5e8d1) at a 135-degree angle. This provides a tactile "soul" to the interface.

---

## 3. Typography: Condensed Authority

The typography utilizes **Plus Jakarta Sans** (condensed) for high-impact displays and **Inter** for utility and data.

| Role | Font Family | Size | Character |
| :--- | :--- | :--- | :--- |
| **Display-LG** | Plus Jakarta Sans | 3.5rem | High-density headings, tracking -0.02em. |
| **Headline-SM** | Plus Jakarta Sans | 1.5rem | Section headers; use Semi-Bold for weight. |
| **Title-SM** | Inter | 1rem | Data category headers. |
| **Body-SM** | Inter | 0.75rem | The workhorse for table data and descriptions. |
| **Label-SM** | Inter | 0.6875rem | Smallest metadata; always Uppercase + 0.05em tracking. |

**The Hierarchy Logic:** We use the condensed nature of Plus Jakarta Sans to fit 20% more information into headlines than standard sans-serifs. The brand identity is conveyed through "Tight & Light"—minimal leading (line height) but generous horizontal margins.

---

## 4. Elevation & Depth: Tonal Layering

We achieve hierarchy through **Tonal Layering** rather than traditional drop shadows.

*   **The Layering Principle:** Depth is "stacked." Place a `surface_container_lowest` (#ffffff) card on a `surface_container_low` (#f3f4f0) section. This creates a "Paper-on-Stone" effect that is sophisticated and legible.
*   **Ambient Shadows:** If a floating element (like a context menu) requires lift, use an "Ambient Blur":
    *   `box-shadow: 0 4px 24px 0 rgba(46, 52, 48, 0.06);` (using `on_surface` color at 6%).
*   **The "Ghost Border" Fallback:** For accessibility in high-density tables, use a "Ghost Border": `outline_variant` (#adb3ae) at **15% opacity**. This provides a guide for the eye without creating a visual cage.

---

## 5. Components

### High-Density Tables (Core Component)
- **Styling:** No vertical or horizontal lines. 
- **Separation:** Use `surface_container_low` for the header row and alternating `surface` / `surface_container_lowest` for rows (zebra striping is too heavy; use hover states instead).
- **Typography:** Use `body-sm` for data cells and `label-md` (Medium weight) for headers.

### Compact Cards
- **Structure:** Use `surface_container_lowest` with a `sm` (0.125rem) or `md` (0.375rem) corner radius.
- **Content:** Information should be "cluster-mapped." Group related data points with 4px of vertical spacing, using `label-sm` in `on_surface_variant` (#5a615c) for captions.

### Buttons & Inputs
- **Primary Button:** `primary` background with `on_primary` text. No border. Use `md` (0.375rem) radius for a modern, architectural feel.
- **Input Fields:** `surface_container_low` background with a `Ghost Border` on focus. Labels should be `label-sm` floating inside the container.
- **Chips:** Use `secondary_container` for neutral filters and `primary_container` for active states. Text must be `label-sm`.

### Data-Driven Overlays
- **Micro-Sparklines:** Use `primary` for positive trends and `error` (#9e422c) for negative. These should be embedded directly within `surface_container_lowest` cards.

---

## 6. Do’s and Don’ts

### Do:
- **Do** lean into asymmetry. It’s okay if a data panel doesn’t span the full width if the content doesn’t require it.
- **Do** use `surface_dim` (#d4dcd5) to pull back secondary information.
- **Do** prioritize "Data-Ink Ratio." Every pixel should serve a piece of information or a clear navigational path.

### Don’t:
- **Don't** use 100% black (#000). Use `on_surface` (#2e3430) for text to maintain the "Stone & Sage" softness.
- **Don't** use standard `lg` or `xl` corner radii for data containers. Large curves waste "corner real estate"; stick to `sm` or `md`.
- **Don't** use dividers. If two elements feel too close, increase the vertical margin using the spacing scale or change the background tone of one element.
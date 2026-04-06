# Design System Documentation: The Digital Naturalist

## 1. Overview & Creative North Star
This design system moves away from the rigid, academic formality of traditional scientific journals toward a philosophy we call **"Tactile Modernism."** 

The Creative North Star is **The Digital Field Guide**: an experience that feels as intentional and curated as a high-end physical journal, but with the fluid accessibility of a contemporary digital product. We achieve this by breaking the "template" look through intentional asymmetry, overlapping elements, and high-contrast typography scales. We replace the heavy serif heritage with a breathable, sans-serif clarity that invites the user into the data rather than lecturing them.

**Design Principles:**
*   **Organic Asymmetry:** Avoid perfect center-alignment. Allow elements to "float" or offset slightly to mimic the way a scientist might tape a specimen into a notebook.
*   **Breathing Room:** Use aggressive whitespace to let the nature-inspired palette provide emotional resonance.
*   **Scientific Precision, Human Warmth:** Use the geometric precision of the typography to ground the soft, organic color shifts.

---

## 2. Colors & Surface Philosophy
The palette is rooted in the deep forest tones of our primary `#2D4B31`, supported by a sophisticated range of biological neutrals.

### The "No-Line" Rule
To achieve a premium, editorial feel, **1px solid borders are prohibited for sectioning.** Structural boundaries must be defined solely through background color shifts. For example, a sidebar should not be "bordered" off; it should simply exist as a `surface-container-low` block sitting atop a `surface` background.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of fine, translucent paper. Use the surface-container tiers to create depth:
*   **Level 0 (Base):** `surface` (#faf9f5)
*   **Level 1 (Sections):** `surface-container-low` (#f4f4ef)
*   **Level 2 (Interactive Elements):** `surface-container` (#eeeeea) or `surface-container-highest` (#e3e3de) for emphasis.

### The "Glass & Gradient" Rule
To prevent the UI from feeling "flat" or "cheap," use **Glassmorphism** for floating overlays (e.g., navigation bars or tooltips). Use semi-transparent surface colors (e.g., `surface` at 80% opacity) with a `backdrop-blur` effect (16px–24px).
*   **Signature Textures:** For Hero sections or Primary CTAs, use a subtle linear gradient (135°) transitioning from `primary` (#17341c) to `primary_container` (#2D4B31). This adds a "soul" to the color that flat hex codes cannot provide.

---

## 3. Typography
We have transitioned from serifs to a dual-sans system to modernize the "Scientific Journal" aesthetic.

*   **Primary Typeface:** *Plus Jakarta Sans* — Used for all Display, Headline, Title, and Body styles. Its modern geometric shapes feel clean and friendly.
*   **Functional Typeface:** *Inter* — Reserved exclusively for `label-md` and `label-sm`. The high x-height and technical clarity of Inter provide the "data-driven" look required for field notes and metadata.

**Hierarchy Strategy:**
*   **Display Styles:** Should be set with tight tracking (-0.02em) to feel authoritative and editorial.
*   **Body Styles:** Use generous line-heights (1.6x) to ensure the scientific data remains accessible and readable.
*   **Contrast:** Pair a `display-sm` headline with a `label-md` in all-caps (Inter) to create a sophisticated, high-end "caption" look.

---

## 4. Elevation & Depth
In this system, depth is conveyed through **Tonal Layering** rather than traditional structural lines or heavy shadows.

*   **The Layering Principle:** Soft, natural lift is achieved by "stacking." A `surface-container-lowest` (#ffffff) card placed on a `surface-container-low` (#f4f4ef) background creates an effortless elevation.
*   **Ambient Shadows:** If a component must "float" (like a Modal or FAB), use shadows that mimic natural ambient light. 
    *   *Formula:* Large blur (32px+), low opacity (4%-8%), using a tinted shadow color based on `on_surface` (#1a1c1a) rather than pure black.
*   **The "Ghost Border" Fallback:** If a border is essential for accessibility, use a **Ghost Border**: `outline_variant` (#c2c8bf) at 20% opacity. Never use 100% opaque borders.
*   **Glassmorphism Depth:** When using glass layers, ensure the `surface_tint` (#47664a) is applied subtly to the overlay to maintain the naturalistic green undertone of the environment.

---

## 5. Components

### Buttons
*   **Primary:** Filled with `primary` (#17341c) or the Signature Gradient. Text is `on_primary`. Roundedness: `md` (0.75rem).
*   **Secondary:** Filled with `secondary_container` (#d6e4d2). No border.
*   **Tertiary:** Ghost style. No background, no border. Use `primary` text.

### Cards & Lists
*   **The Divider Rule:** Forbid the use of divider lines. Use vertical white space (1.5rem to 2rem) or subtle background shifts (e.g., alternating between `surface` and `surface-container-low`) to separate content.
*   **Cards:** Use `lg` (1rem) roundedness. Cards should not have shadows unless they are draggable.

### Input Fields
*   **Visual Style:** Use the "soft-fill" approach. No bottom line, no full border. Use a `surface-container-highest` background with a `sm` (0.25rem) corner radius.
*   **Active State:** The border should only appear on focus, using the `primary` (#17341c) color at 2px thickness.

### Field Notes (Custom Component)
*   A specific layout pattern for scientific data. A `surface-container-low` container with a "Ghost Border" and `label-md` (Inter) headers in all-caps to denote technical metadata.

---

## 6. Do's and Don'ts

### Do:
*   **DO** use asymmetric margins (e.g., 80px left, 120px right) for long-form editorial content.
*   **DO** use the `primary_fixed` color (#c8ecc8) for highlighting important text or data points; it acts like a natural highlighter.
*   **DO** ensure all interactive states (hover/press) use a subtle shift in the `surface_container` tier rather than a color change.

### Don't:
*   **DON'T** use 1px solid black or grey lines to separate content.
*   **DON'T** use standard Material Design "Drop Shadows." They break the organic feel of the field-journal aesthetic.
*   **DON'T** center-align long blocks of text. Stick to left-aligned editorial layouts.
*   **DON'T** use pure #000000 for text. Use `on_surface` (#1a1c1a) to maintain the soft, natural contrast.
---
name: Native Utility System
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1c1b1b'
  on-surface-variant: '#414755'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#717786'
  outline-variant: '#c1c6d7'
  surface-tint: '#005bc1'
  primary: '#0058bc'
  on-primary: '#ffffff'
  primary-container: '#0070eb'
  on-primary-container: '#fefcff'
  inverse-primary: '#adc6ff'
  secondary: '#4c4aca'
  on-secondary: '#ffffff'
  secondary-container: '#6664e4'
  on-secondary-container: '#fffbff'
  tertiary: '#9e3d00'
  on-tertiary: '#ffffff'
  tertiary-container: '#c64f00'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004493'
  secondary-fixed: '#e2dfff'
  secondary-fixed-dim: '#c2c1ff'
  on-secondary-fixed: '#0c006a'
  on-secondary-fixed-variant: '#3631b4'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb595'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7c2e00'
  background: '#fcf9f8'
  on-background: '#1c1b1b'
  surface-variant: '#e5e2e1'
typography:
  display:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  header-section:
    fontFamily: Public Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-large:
    fontFamily: Public Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-main:
    fontFamily: Public Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  input-text:
    fontFamily: Public Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 24px
  label-bold:
    fontFamily: Public Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  caption:
    fontFamily: Public Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  sidebar_width: 260px
  gutter: 20px
---

## Brand & Style

This design system is built upon the "Native OS Utility" aesthetic, prioritizing predictability, durability, and institutional trust. It targets power users and professionals who require a local automation tool that feels like a permanent fixture of their operating system rather than a transient web application.

The style is a refined blend of **Minimalism** and **Corporate Modern**. It avoids decorative flourishes in favor of functional clarity. The emotional response is one of "calm capability"—the interface stays out of the way until needed, providing a grounded workspace where complex automation logic feels structured and safe. Every interaction is explicit; there are no hidden hover states or "mystery meat" navigation, ensuring the tool feels reliable and accessible.

## Colors

The palette is strictly limited to support a Light Mode environment that mimics high-quality system utilities. 

- **Backgrounds:** The primary workspace uses a pure white (#ffffff) to maximize contrast for text. The sidebar utilizes a cool light gray (#f8fafc) to provide clear structural compartmentalization without visual heaviness.
- **Typography:** All primary content uses Dark Charcoal (#1a1a1a) to ensure AAA accessibility and a "printed ink" feel. 
- **Accents:** A classic System Blue is used sparingly for primary actions and active states, ensuring users can immediately identify the "path of least resistance."
- **Borders:** Subtle borders (#e2e8f0) replace shadows as the primary method for defining element boundaries, creating a flat, organized appearance.

## Typography

The typography uses **Public Sans**, an institutional typeface designed for accessibility and clarity. The scale is intentionally enlarged to prevent eye strain during long automation-building sessions.

- **Legibility First:** The minimum body size is 16px. For inputs and interactive fields where data entry occurs, the size is increased to 18px to provide a generous hit target and clear visual feedback.
- **Hierarchy:** High contrast in weight (400 vs 600) is used rather than excessive scale differences to maintain a compact "utility" feel.
- **Spacing:** Line heights are generous (1.5x) to ensure that even dense lists of automation steps remain scannable.

## Layout & Spacing

The layout follows a **Fixed-Fluid Hybrid** model typical of desktop applications. A fixed-width sidebar (260px) anchors the navigation, while the main content area expands to fill the remaining horizontal space, utilizing a logical column-based alignment for form elements.

- **Rhythm:** A 4px baseline grid governs all spacing. 16px (md) is the standard padding for containers, while 24px (lg) is used for major section margins.
- **Visual Gaps:** Automation "nodes" or blocks should be separated by 12px to maintain a sense of connection while clearly defining individual steps.
- **Touch/Click Targets:** All interactive elements must maintain a minimum height of 44px to ensure high hit-accuracy.

## Elevation & Depth

This design system avoids excessive layering, opting for a "flat-plus" approach. Depth is communicated through **Tonal Layers** and **Low-contrast outlines**.

- **Surface Tiers:** The bottom-most layer is the Canvas (#f1f5f9). Components like automation cards or settings panels sit on this canvas using the Primary Background (#ffffff).
- **Shadows:** Only used to indicate "active" or "floating" states (e.g., a card being dragged). Shadows are tight and neutral: `0 2px 4px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.1)`.
- **Dividers:** Horizontal rules should be used to separate logical groups within a single surface, utilizing the Subtle Border color (#e2e8f0).

## Shapes

The shape language is "Soft" (Level 1), utilizing a 4px (0.25rem) standard border radius. This radius provides a professional, organized look that feels modern without becoming "playful" or overly consumer-focused.

- **Standard Elements:** Buttons, checkboxes, and input fields use the 4px radius.
- **Large Containers:** Cards and modals may use the `rounded-lg` (8px) variant to better frame internal content.
- **Icons:** Should follow the same logic—avoiding sharp 90-degree corners in favor of slightly softened terminals.

## Components

Components are designed for "high-intent" interaction, emphasizing clarity over density.

- **Buttons:** Large (44px height), high-contrast. Primary buttons use a solid fill; secondary buttons use a white background with a 1px Strong Border (#cbd5e1). Text is centered and bold.
- **Input Fields:** 18px text, 12px internal padding. Borders are #cbd5e1 and darken to the primary accent color on focus. Labels are always visible above the field.
- **Automation Cards:** White backgrounds with a subtle border. Use a "handle" icon on the left to indicate drag-and-drop capability. No hidden menus; all actions (delete, duplicate, edit) are represented by visible icon-buttons.
- **Checkboxes & Radios:** Scaled up to 20x20px. They use the Primary Color for the "checked" state to ensure high visibility.
- **Sidebar Nav:** Uses a "selected" pill background in a slightly darker gray or light blue to clearly indicate current location. Icons are weighted (2pt stroke) for legibility.
- **Status Badges:** Use a "Stoplight" system (Green/Yellow/Red) for automation status, but always accompany the color with a text label for accessibility.
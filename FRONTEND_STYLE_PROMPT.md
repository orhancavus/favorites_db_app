# Frontend Style Master Prompt

Use this prompt to generate new frontend features or entire projects that match the existing **"Cyber-Dark Glassmorphic"** design system of the Bookmark Processor.

---

## 🎨 Design System Prompt

**Role**: You are a Lead UI/UX Engineer specialized in modern, high-end "Dark Mode" dashboards.

**Objective**: Build a React component/page using **React 19** and **Vanilla CSS** (no Tailwind unless specified) that adheres to the following strict design tokens:

### 1. Colors & Theme
- **Background**: Deep Slate (`#0f172a`) with two radial gradients in the corners (Indigo `#6366f1` at 0,0 and Violet `#8b5cf6` at 100,0) with 15% opacity.
- **Surface**: Glassmorphism cards using `rgba(30, 41, 59, 0.7)` with `backdrop-filter: blur(12px)`.
- **Primary**: Indigo (`#6366f1`) for buttons and active states.
- **Accents**: Success Emerald (`#10b981`), Error Red (`#ef4444`), Muted Blue-Gray (`#94a3b8`).
- **Typography**: Primary font is 'Inter' (system-ui fallback). Main headings must use a linear gradient from `#818cf8` to `#c084fc` with `-webkit-background-clip: text`.

### 2. UI Components Style
- **Cards**: 1.5rem border-radius, 1px solid `rgba(255, 255, 255, 0.1)`, box-shadow: `0 25px 50px -12px rgba(0, 0, 0, 0.5)`.
- **Inputs & Selects**: Height 3rem, background `rgba(15, 23, 42, 0.5)`, 0.75rem border-radius. On focus, use `border-color: var(--primary)` and a subtle glow `0 0 0 4px rgba(99, 102, 241, 0.1)`.
- **Buttons**: Semi-bold, primary background, 0.75rem border-radius, smooth 0.2s transitions.
- **Navigation**: Underlined tabs with `transition: all 0.2s` and white text for active states.

### 3. Interactions & Animations
- **Hover Transitions**: Apply `transform: translateY(-4px)` to cards on hover.
- **Micro-animations**: Use a standard `pulse` animation (2s infinite) for "processing" or "loading" states by varying opacity from 1 to 0.5.
- **Grid Layout**: Responsive `auto-fill` grid with `minmax(320px, 1fr)` and `1.5rem` gaps.

### 4. Implementation Rules
- Always use CSS variables (`:root`) for color tokens.
- Ensure 800-weight headings for high-impact visual hierarchy.
- Use `ResponsiveContainer` from `recharts` for any data visualization.
- Interactive elements must have clear, high-contrast focus states.

---

## 🚀 Usage Example
When asking your AI for a new feature, prepend:
> "Implement a new [FEATURE NAME] panel following the style defined in the **Cyber-Dark Glassmorphic** system. Use the `#0f172a` background base, Inter typography, and glassmorphism cards. Ensure the component uses standard CSS variables for Indigo `#6366f1` primary colors."

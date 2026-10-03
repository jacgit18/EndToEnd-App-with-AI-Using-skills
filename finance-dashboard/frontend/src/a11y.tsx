import type { ReactNode } from "react";

// Text for screen readers only (e.g. the header of an actions column).
export function VisuallyHidden({ children }: { children: ReactNode }) {
  return (
    <span
      style={{
        position: "absolute",
        width: 1,
        height: 1,
        margin: -1,
        padding: 0,
        overflow: "hidden",
        clip: "rect(0 0 0 0)",
        whiteSpace: "nowrap",
        border: 0,
      }}
    >
      {children}
    </span>
  );
}

// Wide tables scroll inside this box instead of making the whole page scroll
// sideways (WCAG 1.4.10 reflow allows two-dimensional content to scroll). It is
// focusable and named so keyboard users can scroll it (axe: scrollable-region-focusable).
export function ScrollTable({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div role="region" aria-label={label} tabIndex={0} style={{ overflowX: "auto", maxWidth: "100%", position: "relative" }}>
      {children}
    </div>
  );
}

// Text colours chosen for 7:1 on white (WCAG AAA 1.4.6).
export const ERROR_TEXT = "#a00000";
export const OK_TEXT = "#1b5e20";

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Vitest runs without globals here (explicit imports keep tsc strict), and RTL
// only auto-unmounts between tests when a global afterEach exists — so do it by hand.
afterEach(cleanup);

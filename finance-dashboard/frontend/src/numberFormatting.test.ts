import { describe, it, expect } from "vitest";
import { formatNumberWithCommas, stripCommas } from "./numberFormatting";

describe("formatNumberWithCommas", () => {
  it("formats simple numbers with commas", () => {
    expect(formatNumberWithCommas("1000")).toBe("1,000");
    expect(formatNumberWithCommas("100000")).toBe("100,000");
    expect(formatNumberWithCommas("1000000")).toBe("1,000,000");
  });

  it("handles decimals correctly", () => {
    expect(formatNumberWithCommas("1000.50")).toBe("1,000.50");
    expect(formatNumberWithCommas("100000.99")).toBe("100,000.99");
  });

  it("handles negative numbers", () => {
    expect(formatNumberWithCommas("-1000")).toBe("-1,000");
    expect(formatNumberWithCommas("-100000")).toBe("-100,000");
    expect(formatNumberWithCommas("-1000.50")).toBe("-1,000.50");
  });

  it("handles empty strings", () => {
    expect(formatNumberWithCommas("")).toBe("");
  });

  it("handles small numbers without commas", () => {
    expect(formatNumberWithCommas("100")).toBe("100");
    expect(formatNumberWithCommas("99")).toBe("99");
    expect(formatNumberWithCommas("100.50")).toBe("100.50");
  });

  it("strips existing commas before formatting", () => {
    expect(formatNumberWithCommas("1,000")).toBe("1,000");
    expect(formatNumberWithCommas("100,000")).toBe("100,000");
  });

  it("handles partial decimal input", () => {
    expect(formatNumberWithCommas("1000.")).toBe("1,000.");
    expect(formatNumberWithCommas("1000.5")).toBe("1,000.5");
  });
});

describe("stripCommas", () => {
  it("removes all commas from a string", () => {
    expect(stripCommas("1,000")).toBe("1000");
    expect(stripCommas("100,000")).toBe("100000");
    expect(stripCommas("1,000.50")).toBe("1000.50");
  });

  it("handles strings without commas", () => {
    expect(stripCommas("1000")).toBe("1000");
    expect(stripCommas("1000.50")).toBe("1000.50");
  });

  it("handles negative numbers with commas", () => {
    expect(stripCommas("-1,000")).toBe("-1000");
    expect(stripCommas("-100,000.50")).toBe("-100000.50");
  });

  it("handles empty strings", () => {
    expect(stripCommas("")).toBe("");
  });
});

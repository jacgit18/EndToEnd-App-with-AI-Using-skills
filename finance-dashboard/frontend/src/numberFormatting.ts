export function formatNumberWithCommas(value: string): string {
  if (!value) return value;

  // Strip any existing commas
  const withoutCommas = value.replace(/,/g, "");

  // Handle negative numbers
  const isNegative = withoutCommas.startsWith("-");
  const absValue = isNegative ? withoutCommas.slice(1) : withoutCommas;

  // Split integer and decimal parts
  const parts = absValue.split(".");
  const integerPart = parts[0];
  const decimalPart = parts[1];

  // Add commas to integer part
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");

  // Reconstruct the number
  let result = isNegative ? "-" + formattedInteger : formattedInteger;
  if (decimalPart !== undefined) {
    result += "." + decimalPart;
  }

  return result;
}

export function stripCommas(value: string): string {
  return value.replace(/,/g, "");
}

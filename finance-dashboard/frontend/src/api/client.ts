import axios from "axios";

export const api = axios.create({ baseURL: "/" });

export interface Transaction {
  id: number;
  account_id: number;
  date: string;
  /** Decimal serialized as a string to preserve precision (see ADR 0001). */
  amount: string;
  description: string;
  category_id: number | null;
}

export type NewTransaction = Omit<Transaction, "id">;

export interface Account {
  id: number;
  name: string;
  type: "checking" | "savings" | "credit_card" | "cash";
  currency: string;
  starting_balance: string;
  archived: boolean;
}

export async function getHealth(): Promise<{ status: string }> {
  const { data } = await api.get("/health");
  return data;
}

export async function listAccounts(): Promise<Account[]> {
  const { data } = await api.get("/api/accounts");
  return data;
}

export async function listTransactions(): Promise<Transaction[]> {
  const { data } = await api.get("/api/transactions");
  return data;
}

export async function createTransaction(
  input: NewTransaction,
): Promise<Transaction> {
  const { data } = await api.post("/api/transactions", input);
  return data;
}

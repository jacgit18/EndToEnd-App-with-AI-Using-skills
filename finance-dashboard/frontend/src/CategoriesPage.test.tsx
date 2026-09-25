import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CategoriesPage from "./CategoriesPage";
import { ApiError, type Category } from "./api/client";

const listCategories = vi.fn();
const createCategory = vi.fn();
const updateCategory = vi.fn();
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: {
    listCategories: (...a: unknown[]) => listCategories(...a),
    createCategory: (...a: unknown[]) => createCategory(...a),
    updateCategory: (...a: unknown[]) => updateCategory(...a),
  },
}));

const cat = (over: Partial<Category> = {}): Category => ({
  id: 1,
  name: "Groceries",
  kind: "expense",
  is_archived: false,
  created_at: "2026-01-01T00:00:00Z",
  ...over,
});

function renderPage() {
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}
    >
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  listCategories.mockReset().mockResolvedValue([cat()]);
  createCategory.mockReset().mockResolvedValue(cat());
  updateCategory.mockReset().mockResolvedValue(cat());
});

describe("CategoriesPage", () => {
  it("lists categories with their kind", async () => {
    renderPage();
    expect(await screen.findByText("Groceries")).toBeInTheDocument();
    expect(screen.getAllByText("Expense").length).toBeGreaterThan(0);
  });

  it("creates a category with a trimmed name and chosen kind", async () => {
    renderPage();
    await screen.findByText("Groceries");
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "  Salary " } });
    fireEvent.change(screen.getByLabelText("Kind"), { target: { value: "income" } });
    fireEvent.click(screen.getByRole("button", { name: "Add category" }));
    await waitFor(() =>
      expect(createCategory).toHaveBeenCalledWith({ name: "Salary", kind: "income" }),
    );
  });

  it("shows the server's error on a duplicate name", async () => {
    createCategory.mockRejectedValue(new ApiError(409, "a category with that name already exists"));
    renderPage();
    await screen.findByText("Groceries");
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Groceries" } });
    fireEvent.click(screen.getByRole("button", { name: "Add category" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("already exists");
  });

  it("requests archived categories only when the box is ticked", async () => {
    renderPage();
    await screen.findByText("Groceries");
    expect(listCategories).toHaveBeenLastCalledWith({ includeArchived: false });
    fireEvent.click(screen.getByLabelText("Show archived"));
    await waitFor(() => expect(listCategories).toHaveBeenLastCalledWith({ includeArchived: true }));
  });

  it("renames, sending only the name", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Rename" }));
    const row = screen.getByRole("button", { name: "Save" }).closest("tr")!;
    fireEvent.change(row.querySelector("input")!, { target: { value: " Food " } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(updateCategory).toHaveBeenCalledWith(1, { name: "Food" }));
  });

  it("closes the editor without a request when the name is unchanged", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Rename" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(updateCategory).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Rename" })).toBeInTheDocument();
  });

  it("archives and unarchives", async () => {
    listCategories.mockResolvedValue([cat(), cat({ id: 2, name: "Old", is_archived: true })]);
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Archive" }));
    await waitFor(() => expect(updateCategory).toHaveBeenCalledWith(1, { is_archived: true }));
    fireEvent.click(screen.getByRole("button", { name: "Unarchive" }));
    await waitFor(() => expect(updateCategory).toHaveBeenCalledWith(2, { is_archived: false }));
    expect(screen.getByText("Old (archived)")).toBeInTheDocument();
  });
});

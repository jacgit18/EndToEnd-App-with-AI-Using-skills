import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./api/client";
import LoginPage from "./LoginPage";

// Only api.login is faked; ApiError stays the real class so the page's
// `instanceof ApiError` check behaves exactly as it does in the app.
const login = vi.fn();
vi.mock("./api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./api/client")>()),
  api: { login: (...args: unknown[]) => login(...args) },
}));

function renderPage() {
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { mutations: { retry: false } } })}>
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<p>Dashboard</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function submit(email = "owner@example.com", password = "pw") {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: email } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: password } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
}

// Braces matter: a function returned from a hook is run by Vitest as cleanup.
beforeEach(() => {
  login.mockReset();
});

describe("LoginPage", () => {
  it("sends the typed credentials and goes to the dashboard on success", async () => {
    login.mockResolvedValue(undefined);
    renderPage();

    submit("owner@example.com", "devpassword");

    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
    expect(login).toHaveBeenCalledWith("owner@example.com", "devpassword");
  });

  it("shows one generic message for a 401, and stays on the page", async () => {
    login.mockRejectedValue(new ApiError(401, "nope"));
    renderPage();

    submit();

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });

  it("tells the owner to wait on a 429", async () => {
    login.mockRejectedValue(new ApiError(429, "slow down"));
    renderPage();

    submit();

    expect(await screen.findByRole("alert")).toHaveTextContent("Too many attempts");
  });

  it("falls back to a connection message for any other failure", async () => {
    login.mockRejectedValue(new TypeError("Failed to fetch"));
    renderPage();

    submit();

    expect(await screen.findByRole("alert")).toHaveTextContent("Couldn't sign in");
  });

  it("disables the button while the request is in flight", async () => {
    login.mockReturnValue(new Promise(() => {})); // never settles
    renderPage();

    submit();

    await waitFor(() => expect(screen.getByRole("button")).toBeDisabled());
    expect(screen.getByRole("button")).toHaveTextContent("Signing in…");
  });
});

// client.ts keeps the CSRF token in a module-level variable, so every test
// re-imports a fresh copy (vi.resetModules) — otherwise one test's login would
// leak its token into the next.
import { beforeEach, describe, expect, it, vi } from "vitest";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

let fetchMock: ReturnType<typeof vi.fn>;
let assign: ReturnType<typeof vi.fn>;

async function loadApi(pathname = "/") {
  vi.resetModules();
  assign = vi.fn();
  vi.stubGlobal("location", { pathname, assign });
  return (await import("./client")).api;
}

const csrfHeaderOf = (call: unknown[]) =>
  (call[1] as RequestInit).headers as Record<string, string>;

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
});

describe("CSRF token handling", () => {
  it("sends the token from login on the next write, without calling /me", async () => {
    const api = await loadApi("/login");
    fetchMock
      .mockResolvedValueOnce(json({ csrf_token: "tok-1" })) // login
      .mockResolvedValueOnce(json({ id: 1 }, 201)); // createAccount

    await api.login("a@b.c", "pw");
    await api.createAccount({ name: "Checking", type: "checking" });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(csrfHeaderOf(fetchMock.mock.calls[1])["X-CSRF-Token"]).toBe("tok-1");
  });

  it("fetches a fresh token from /auth/me before a write after a reload", async () => {
    const api = await loadApi(); // fresh module = reloaded page, no token in memory
    fetchMock
      .mockResolvedValueOnce(json({ csrf_token: "tok-me" })) // /auth/me
      .mockResolvedValueOnce(json({ id: 1 }, 201)); // createAccount

    await api.createAccount({ name: "Checking", type: "checking" });

    expect(fetchMock.mock.calls[0][0]).toBe("/api/auth/me");
    expect(csrfHeaderOf(fetchMock.mock.calls[1])["X-CSRF-Token"]).toBe("tok-me");
  });

  it("does not send a CSRF header on reads", async () => {
    const api = await loadApi();
    fetchMock.mockResolvedValueOnce(json([]));

    await api.listAccounts();

    expect(csrfHeaderOf(fetchMock.mock.calls[0])).not.toHaveProperty("X-CSRF-Token");
  });
});

describe("401 handling", () => {
  it("redirects to /login when a request comes back 401", async () => {
    const api = await loadApi("/");
    fetchMock.mockResolvedValueOnce(json({ detail: "Not authenticated" }, 401));

    await expect(api.listAccounts()).rejects.toMatchObject({ status: 401 });

    expect(assign).toHaveBeenCalledWith("/login");
  });

  it("does not redirect on /login, where 401 means a wrong password", async () => {
    const api = await loadApi("/login");
    fetchMock.mockResolvedValueOnce(json({ detail: "Invalid email or password" }, 401));

    await expect(api.login("a@b.c", "bad")).rejects.toMatchObject({ status: 401 });

    expect(assign).not.toHaveBeenCalled();
  });
});

describe("logout", () => {
  it("handles the empty 204 and forgets the token", async () => {
    const api = await loadApi("/login");
    fetchMock
      .mockResolvedValueOnce(json({ csrf_token: "tok-1" })) // login
      .mockResolvedValueOnce(new Response(null, { status: 204 })) // logout
      .mockResolvedValueOnce(json({ csrf_token: "tok-2" })) // /auth/me
      .mockResolvedValueOnce(json({ id: 1 }, 201)); // createAccount

    await api.login("a@b.c", "pw");
    await expect(api.logout()).resolves.toBeUndefined();
    await api.createAccount({ name: "Checking", type: "checking" });

    // The token was cleared, so the write had to go get a new one.
    expect(fetchMock.mock.calls[2][0]).toBe("/api/auth/me");
    expect(csrfHeaderOf(fetchMock.mock.calls[3])["X-CSRF-Token"]).toBe("tok-2");
  });
});

describe("account calls", () => {
  it("listAccounts hides archived by default and asks for them on request", async () => {
    const api = await loadApi();
    fetchMock.mockImplementation(async () => json([]));

    await api.listAccounts();
    await api.listAccounts({ includeArchived: true });

    expect(fetchMock.mock.calls[0][0]).toBe("/api/accounts");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/accounts?include_archived=true");
  });

  it("updateAccount PATCHes only the given fields, with the CSRF token", async () => {
    const api = await loadApi();
    fetchMock
      .mockResolvedValueOnce(json({ csrf_token: "tok" })) // /auth/me
      .mockResolvedValueOnce(json({ id: 7 }));

    await api.updateAccount(7, { is_archived: true });

    const [url, init] = fetchMock.mock.calls[1];
    expect(url).toBe("/api/accounts/7");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body)).toEqual({ is_archived: true });
    expect(csrfHeaderOf(fetchMock.mock.calls[1])["X-CSRF-Token"]).toBe("tok");
  });
});

describe("multipart uploads", () => {
  it("sends FormData with the CSRF header and NO Content-Type (browser sets the boundary)", async () => {
    const api = await loadApi();
    fetchMock
      .mockResolvedValueOnce(json({ csrf_token: "tok-up" })) // /auth/me
      .mockResolvedValueOnce(json({ headers: [], rows: [], row_count: 0, delimiter: ",", distinct_values: {} }));

    await api.previewImport(new File(["a,b\n1,2\n"], "x.csv"));

    const init = fetchMock.mock.calls[1][1] as RequestInit;
    expect(init.body).toBeInstanceOf(FormData);
    expect((init.headers as Record<string, string>)["X-CSRF-Token"]).toBe("tok-up");
    expect(init.headers as Record<string, string>).not.toHaveProperty("Content-Type");
  });

  it("createImport omits account_id in multi-account mode and sends the mapping as JSON text", async () => {
    const api = await loadApi();
    fetchMock.mockResolvedValueOnce(json({ csrf_token: "t" })).mockResolvedValueOnce(json({ batch_id: 1 }, 201));
    const mapping = {
      date_column: "d", amount_column: "a", description_column: "n", date_format: "iso" as const,
      invert_sign: false, account_column: "acct", account_map: { X: 3, Y: null },
    };

    await api.createImport(new File(["x"], "x.csv"), mapping);

    const form = (fetchMock.mock.calls[1][1] as RequestInit).body as FormData;
    expect(form.has("account_id")).toBe(false);
    expect(JSON.parse(form.get("mapping") as string)).toEqual(mapping);
  });
});

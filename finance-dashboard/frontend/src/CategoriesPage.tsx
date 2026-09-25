import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api, CATEGORY_KINDS, type Category, type CategoryCreate, type CategoryKind, type CategoryUpdate } from "./api/client";

export const KIND_LABELS: Record<CategoryKind, string> = {
  expense: "Expense",
  income: "Income",
};

export default function CategoriesPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [kind, setKind] = useState<CategoryKind>("expense");
  const [showArchived, setShowArchived] = useState(false);

  // Own cache key per view; invalidating the bare ["categories"] prefix refreshes all.
  const categories = useQuery({
    queryKey: ["categories", { includeArchived: showArchived }],
    queryFn: () => api.listCategories({ includeArchived: showArchived }),
  });

  const createCategory = useMutation({
    mutationFn: (body: CategoryCreate) => api.createCategory(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setName("");
      setKind("expense");
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    createCategory.mutate({ name: name.trim(), kind });
  }

  return (
    <section style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <p>
        <Link to="/">← Transactions</Link>
      </p>
      <h2>Categories</h2>

      <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
        <label>
          Name <input required value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Kind{" "}
          <select value={kind} onChange={(e) => setKind(e.target.value as CategoryKind)}>
            {CATEGORY_KINDS.map((k) => (
              <option key={k} value={k}>
                {KIND_LABELS[k]}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={createCategory.isPending}>
          Add category
        </button>
      </form>

      {createCategory.isError && (
        <p role="alert" style={{ color: "crimson" }}>{(createCategory.error as Error).message}</p>
      )}

      <label style={{ display: "block", margin: "0.5rem 0" }}>
        <input
          type="checkbox"
          checked={showArchived}
          onChange={(e) => setShowArchived(e.target.checked)}
        />{" "}
        Show archived
      </label>

      <table>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Name</th>
            <th style={{ textAlign: "left" }}>Kind</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {categories.data?.map((c) => (
            <CategoryRow key={c.id} category={c} />
          ))}
        </tbody>
      </table>
    </section>
  );
}

function CategoryRow({ category: c }: { category: Category }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(c.name);

  const update = useMutation({
    mutationFn: (body: CategoryUpdate) => api.updateCategory(c.id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setEditing(false);
    },
  });

  function startEditing() {
    setName(c.name);
    update.reset();
    setEditing(true);
  }

  function save() {
    // Backend rejects an empty PATCH, so an unchanged name just closes the editor.
    if (name.trim() === c.name) return setEditing(false);
    update.mutate({ name: name.trim() });
  }

  const error = update.isError && (
    <span role="alert" style={{ color: "crimson" }}> {(update.error as Error).message}</span>
  );

  if (!editing) {
    return (
      <tr style={c.is_archived ? { opacity: 0.55 } : undefined}>
        <td>
          {c.name}
          {c.is_archived && " (archived)"}
        </td>
        <td>{KIND_LABELS[c.kind]}</td>
        <td>
          <button onClick={startEditing}>Rename</button>{" "}
          <button
            onClick={() => update.mutate({ is_archived: !c.is_archived })}
            disabled={update.isPending}
          >
            {c.is_archived ? "Unarchive" : "Archive"}
          </button>
          {error}
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td>
        <input aria-label="Name" value={name} onChange={(e) => setName(e.target.value)} />
      </td>
      <td>{KIND_LABELS[c.kind]}</td>
      <td>
        <button onClick={save} disabled={update.isPending || name.trim() === ""}>
          Save
        </button>{" "}
        <button onClick={() => setEditing(false)}>Cancel</button>
        {error}
      </td>
    </tr>
  );
}

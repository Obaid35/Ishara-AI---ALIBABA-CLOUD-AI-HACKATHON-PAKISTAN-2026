"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, get, patch, post } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Card, Empty, PageHeader, Toast, useToast } from "@/components/admin/ui";

interface UserRow {
  id: string;
  email: string;
  full_name: string;
  role_code: string;
  is_active: boolean;
  must_change_password: boolean;
  last_login_at: string | null;
}

const ROLES = ["doctor", "staff", "admin"];

export default function UsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<UserRow[]>([]);
  const [creating, setCreating] = useState(false);
  const [temporary, setTemporary] = useState<{ email: string; password: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const [form, setForm] = useState({
    email: "",
    full_name: "",
    role_code: "doctor",
    password: "",
  });

  const load = useCallback(() => {
    get<{ users: UserRow[] }>("/api/admin/users")
      .then((data) => setUsers(data.users))
      .catch(() => setUsers([]));
  }, []);

  useEffect(load, [load]);

  const update = async (row: UserRow, body: Record<string, unknown>) => {
    setBusy(true);
    try {
      await patch(`/api/admin/users/${row.id}`, body);
      toast.ok(`${row.email} updated.`);
      load();
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  };

  const create = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      await post("/api/admin/users", form);
      toast.ok(`${form.email} created. They must change their password on first sign-in.`);
      setForm({ email: "", full_name: "", role_code: "doctor", password: "" });
      setCreating(false);
      load();
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Could not create the account.");
    } finally {
      setBusy(false);
    }
  };

  const resetPassword = async (row: UserRow) => {
    setBusy(true);
    try {
      const result = await post<{ temporary_password: string }>(
        `/api/admin/users/${row.id}/reset-password`,
      );
      setTemporary({ email: row.email, password: result.temporary_password });
      load();
    } catch {
      toast.fail("Could not reset the password.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Users"
        description="Accounts are created here — there is no public sign-up"
        actions={
          <button onClick={() => setCreating(true)} className="btn-sm h-10 px-4 border-brand text-brand">
            Add account
          </button>
        }
      />

      <div className="p-6 max-w-[1200px]">
        <Card>
          {users.length === 0 ? (
            <Empty>No accounts.</Empty>
          ) : (
            <table className="w-full">
              <thead>
                <tr>
                  <th className="th">Name</th>
                  <th className="th">Email</th>
                  <th className="th">Role</th>
                  <th className="th">Last sign-in</th>
                  <th className="th">Active</th>
                  <th className="th"></th>
                </tr>
              </thead>
              <tbody>
                {users.map((row) => {
                  const self = row.id === me?.id;
                  return (
                    <tr key={row.id} className="hover:bg-page/60">
                      <td className="td">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{row.full_name || "—"}</span>
                          {self && <span className="pill-neutral text-[10px] py-0">you</span>}
                          {row.must_change_password && (
                            <span className="pill-warn text-[10px] py-0">must change password</span>
                          )}
                        </div>
                      </td>
                      <td className="td text-muted">{row.email}</td>
                      <td className="td">
                        <select
                          value={row.role_code}
                          onChange={(event) => update(row, { role_code: event.target.value })}
                          disabled={busy || self}
                          title={self ? "You cannot change your own role" : undefined}
                          className="h-8 px-2 rounded-lg border border-line bg-surface text-xs capitalize disabled:opacity-40"
                        >
                          {ROLES.map((role) => (
                            <option key={role} value={role}>
                              {role}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="td text-xs text-muted">
                        {row.last_login_at
                          ? new Date(row.last_login_at).toLocaleString()
                          : "never"}
                      </td>
                      <td className="td">
                        <button
                          onClick={() => update(row, { is_active: !row.is_active })}
                          disabled={busy || self}
                          title={self ? "You cannot deactivate your own account" : undefined}
                          className={`relative w-11 h-6 rounded-full transition-colors disabled:opacity-30 ${
                            row.is_active ? "bg-brand" : "bg-slate-300"
                          }`}
                        >
                          <span
                            className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                              row.is_active ? "translate-x-[22px]" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                      </td>
                      <td className="td text-right">
                        <button
                          onClick={() => void resetPassword(row)}
                          disabled={busy}
                          className="btn-sm"
                        >
                          Reset password
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </Card>

        <p className="text-xs text-muted mt-3">
          Deactivating an account revokes its active sessions immediately. Passwords are hashed and
          are never displayed, emailed or written to the audit log.
        </p>
      </div>

      {creating && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4">
          <form onSubmit={create} className="card w-full max-w-md p-6 space-y-4">
            <h3 className="font-semibold">New staff account</h3>

            <div>
              <label className="label">Full name</label>
              <input
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                required
                className="input"
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                required
                placeholder="name@hospital.local"
                className="input"
              />
            </div>
            <div>
              <label className="label">Role</label>
              <select
                value={form.role_code}
                onChange={(event) => setForm({ ...form, role_code: event.target.value })}
                className="input capitalize"
              >
                {ROLES.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Temporary password</label>
              <input
                type="text"
                value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
                required
                minLength={8}
                className="input font-mono"
              />
              <p className="text-[11px] text-muted mt-1.5">
                At least 8 characters. They will be required to change it on first sign-in.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button type="button" onClick={() => setCreating(false)} className="btn-sm h-10 px-4">
                Cancel
              </button>
              <button
                type="submit"
                disabled={busy}
                className="btn h-10 px-4 bg-brand text-white hover:bg-brand-hover text-sm"
              >
                {busy ? "Creating…" : "Create account"}
              </button>
            </div>
          </form>
        </div>
      )}

      {temporary && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4">
          <div className="card w-full max-w-md p-6">
            <h3 className="font-semibold">Temporary password</h3>
            <p className="text-sm text-muted mt-2">
              Hand this to <strong className="text-ink">{temporary.email}</strong> directly. It is
              shown once and is not stored anywhere.
            </p>
            <div className="mt-4 p-3 rounded-lg bg-page border border-line font-mono text-center text-lg select-all">
              {temporary.password}
            </div>
            <button
              onClick={() => setTemporary(null)}
              className="btn h-10 px-4 w-full mt-4 bg-brand text-white hover:bg-brand-hover text-sm"
            >
              Done
            </button>
          </div>
        </div>
      )}

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, get, patch } from "@/lib/api";
import { Card, Empty, PageHeader, StatusPill, Toast, useToast } from "@/components/admin/ui";

interface AssetRow {
  id: string;
  kind: string;
  path: string;
  bytes: number;
  source_name: string | null;
  permission_status: string | null;
  permitted_development: boolean | null;
  permitted_internal_testing: boolean | null;
  permitted_demo_playback: boolean | null;
  permitted_public_release: boolean | null;
  license_notes: string | null;
  used_by_phrases: string | null;
  used_by_messages: string | null;
}

const PERMISSIONS = [
  ["permitted_development", "Development"],
  ["permitted_internal_testing", "Internal testing"],
  ["permitted_demo_playback", "Demo playback"],
  ["permitted_public_release", "Public release"],
] as const;

const STATUSES = ["unknown", "requested", "granted", "denied", "own_recording"];

export default function AssetsPage() {
  const [assets, setAssets] = useState<AssetRow[]>([]);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const load = useCallback(() => {
    get<{ assets: AssetRow[] }>("/api/admin/assets")
      .then((data) => setAssets(data.assets))
      .catch(() => setAssets([]));
  }, []);

  useEffect(load, [load]);

  const update = async (row: AssetRow, body: Record<string, unknown>) => {
    setBusy(true);
    try {
      await patch(`/api/admin/assets/${row.id}/rights`, body);
      load();
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  };

  const gaps = assets.filter(
    (a) =>
      (a.used_by_phrases || a.used_by_messages) &&
      (!a.permission_status || ["unknown", "requested"].includes(a.permission_status)),
  ).length;

  return (
    <>
      <PageHeader
        title="Assets & rights"
        description="Four independent permissions — helping the project does not imply public release"
        actions={
          gaps > 0 ? (
            <span className="pill-danger">{gaps} permission gaps</span>
          ) : (
            <span className="pill-ok">No gaps</span>
          )
        }
      />

      <div className="p-6 max-w-[1500px]">
        <Card>
          {assets.length === 0 ? (
            <Empty>No assets registered.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1150px]">
                <thead>
                  <tr>
                    <th className="th">File</th>
                    <th className="th">Source</th>
                    <th className="th">Status</th>
                    {PERMISSIONS.map(([key, label]) => (
                      <th key={key} className="th text-center">
                        {label}
                      </th>
                    ))}
                    <th className="th">Used by</th>
                  </tr>
                </thead>
                <tbody>
                  {assets.map((row) => (
                    <tr key={row.id} className="hover:bg-page/60">
                      <td className="td">
                        <div className="font-mono text-[11px]">{row.path}</div>
                        <div className="text-[10px] text-muted mt-0.5">
                          {row.kind.replace("_", " ")} · {(row.bytes / 1024).toFixed(0)} KB
                        </div>
                      </td>
                      <td className="td text-xs text-muted max-w-[160px] truncate">
                        {row.source_name || "—"}
                      </td>
                      <td className="td">
                        <select
                          value={row.permission_status ?? "unknown"}
                          onChange={(event) =>
                            update(row, { permission_status: event.target.value })
                          }
                          disabled={busy}
                          className="h-8 px-2 rounded-lg border border-line bg-surface text-xs"
                        >
                          {STATUSES.map((status) => (
                            <option key={status} value={status}>
                              {status.replace(/_/g, " ")}
                            </option>
                          ))}
                        </select>
                      </td>
                      {PERMISSIONS.map(([key]) => (
                        <td key={key} className="td text-center">
                          <input
                            type="checkbox"
                            checked={Boolean(row[key])}
                            onChange={(event) => update(row, { [key]: event.target.checked })}
                            disabled={busy}
                            className="w-4 h-4 accent-[#017A3A] cursor-pointer"
                          />
                        </td>
                      ))}
                      <td className="td text-[11px] text-muted max-w-[180px]">
                        {row.used_by_phrases || row.used_by_messages || (
                          <span className="opacity-50">unused</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card p-4 text-xs text-muted">
            <strong className="text-ink font-medium">Viewing is not redistributing.</strong> If a
            third-party video is downloaded, embedded, bundled or displayed, the permission basis
            must be recorded here. A phrase cannot be enabled unless its video has demo-playback
            permission — the database refuses it.
          </div>
          <div className="card p-4 text-xs text-muted">
            <strong className="text-ink font-medium">Placeholders are not verified content.</strong>{" "}
            Assets seeded as placeholders are our own generated files. Replace them with verified
            PSL recordings and re-enter the rights before any real demo.
          </div>
        </div>
      </div>

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}

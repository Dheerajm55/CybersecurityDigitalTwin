import { useNavigate } from "react-router-dom";
import { Asset } from "../types";
import RiskBadge from "./RiskBadge";

interface Props {
  assets: Asset[];
}

export default function AssetTable({ assets }: Props) {
  const navigate = useNavigate();

  return (
    <div className="overflow-x-auto border border-border rounded-lg bg-surface">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-bg text-left text-subtext">
            <th className="px-4 py-2.5 font-medium">Asset</th>
            <th className="px-4 py-2.5 font-medium">Type</th>
            <th className="px-4 py-2.5 font-medium">Criticality</th>
            <th className="px-4 py-2.5 font-medium">Risk</th>
            <th className="px-4 py-2.5 font-medium">MFA</th>
            <th className="px-4 py-2.5 font-medium">Exposure</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((a) => (
            <tr
              key={a.id}
              onClick={() => navigate(`/assets/${a.id}`)}
              className="border-b border-border last:border-0 hover:bg-bg cursor-pointer transition-colors"
            >
              <td className="px-4 py-2.5">
                <div className="font-medium text-text">{a.name}</div>
                <div className="text-xs text-subtext">{a.owner || "Unassigned"}</div>
              </td>
              <td className="px-4 py-2.5 text-subtext">{a.asset_type.replaceAll("_", " ")}</td>
              <td className="px-4 py-2.5 text-subtext">{a.criticality}</td>
              <td className="px-4 py-2.5">
                <RiskBadge level={a.risk_class} size="sm" />
                <span className="ml-2 text-xs text-subtext">{a.risk_score}/100</span>
              </td>
              <td className="px-4 py-2.5">
                <span className={a.mfa_enabled ? "text-success" : "text-danger"}>
                  {a.mfa_enabled ? "Enabled" : "Disabled"}
                </span>
              </td>
              <td className="px-4 py-2.5">
                <span className={a.internet_exposed ? "text-warning" : "text-subtext"}>
                  {a.internet_exposed ? "Public" : "Internal"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

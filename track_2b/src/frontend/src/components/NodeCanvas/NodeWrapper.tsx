"use client";

import { Handle, Position } from "@xyflow/react";

interface Props {
  badge: string;
  title: string;
  description?: string;
  children: React.ReactNode;
  hasTarget?: boolean;
  hasSource?: boolean;
}

const handleStyle: React.CSSProperties = {
  background: "#D4A520",
  width: 10,
  height: 10,
  border: "2px solid #6B4226",
  boxShadow: "0 0 6px rgba(212,165,32,0.4)",
};

export default function NodeWrapper({
  badge,
  title,
  description,
  children,
  hasTarget = true,
  hasSource = true,
}: Props) {
  return (
    <div style={{ position: "relative" }}>
      {hasTarget && (
        <Handle type="target" position={Position.Left} style={handleStyle} />
      )}
      <div
        className="cursor-grab active:cursor-grabbing"
        style={{
          background: "#FDF5E6",
          border: "3px solid #6B4226",
          borderRadius: "6px",
          boxShadow:
            "inset 2px 2px 0 rgba(196,164,108,.5), inset -2px -2px 0 rgba(61,37,16,.2), 3px 3px 0 rgba(61,37,16,.35)",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          className="px-3 py-2"
          style={{
            background: "#E8D5A3",
            borderBottom: "2px solid #C4A46C",
          }}
        >
          <div className="flex items-center gap-2">
            <span
              className="text-[12px] font-pixel px-1.5 py-0.5 rounded leading-none"
              style={{
                color: "#6B4C2A",
                background: "rgba(212,165,32,0.2)",
                border: "1px solid #C4A46C",
              }}
            >
              {badge}
            </span>
            <span
              className="text-[15px] font-pixel tracking-tight"
              style={{ color: "#3D2510" }}
            >
              {"\u2605"} {title}
            </span>
          </div>
          {description && (
            <p
              className="mt-1 text-[13px] font-mono leading-tight uppercase tracking-widest"
              style={{
                color: "#8B7355",
                borderLeft: "2px solid #C4A46C",
                paddingLeft: "8px",
              }}
            >
              {description}
            </p>
          )}
        </div>
        {/* Content */}
        <div className="p-3">{children}</div>
      </div>
      {hasSource && (
        <Handle type="source" position={Position.Right} style={handleStyle} />
      )}
    </div>
  );
}

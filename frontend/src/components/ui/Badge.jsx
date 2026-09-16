import React from "react";
import { cn } from "../../utils/cn";
import { Loader2 } from "lucide-react";

export function Badge({
  children,
  variant = "default",
  status,
  size = "sm",
  className = "",
  ...props
}) {
  // If status is provided, map to semantic status styles
  let resolvedVariant = variant;
  if (status) {
    switch (status.toUpperCase()) {
      case "READY":
        resolvedVariant = "success";
        break;
      case "PROCESSING":
        resolvedVariant = "processing";
        break;
      case "QUEUED":
        resolvedVariant = "warning";
        break;
      case "FAILED":
        resolvedVariant = "error";
        break;
      default:
        resolvedVariant = "default";
    }
  }

  const variantStyles = {
    default: "bg-[#181B22] text-text-secondary border-border",
    primary: "bg-primary/15 text-primary-hover border-primary/30",
    success: "bg-status-success/10 text-emerald-400 border-status-success/20",
    warning: "bg-status-warning/10 text-amber-400 border-status-warning/20",
    error: "bg-status-error/10 text-rose-400 border-status-error/20",
    processing: "bg-primary/10 text-primary-hover border-primary/25",
  };

  const sizeStyles = {
    xs: "px-2 py-0.5 text-[11px]",
    sm: "px-2.5 py-0.5 text-xs",
    md: "px-3 py-1 text-xs",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-medium border rounded-full select-none",
        variantStyles[resolvedVariant] || variantStyles.default,
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {resolvedVariant === "processing" ? (
        <Loader2 className="h-3 w-3 animate-spin text-current shrink-0" />
      ) : resolvedVariant === "success" ? (
        <span className="h-1.5 w-1.5 rounded-full bg-status-success shrink-0" />
      ) : resolvedVariant === "warning" ? (
        <span className="h-1.5 w-1.5 rounded-full bg-status-warning shrink-0" />
      ) : resolvedVariant === "error" ? (
        <span className="h-1.5 w-1.5 rounded-full bg-status-error shrink-0" />
      ) : null}
      <span>{children || status}</span>
    </span>
  );
}

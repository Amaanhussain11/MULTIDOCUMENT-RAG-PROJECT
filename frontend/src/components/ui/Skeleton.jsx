import React from "react";
import { cn } from "../../utils/cn";

export function Skeleton({ className = "", ...props }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-[#181B22]/80 border border-border/40",
        className
      )}
      {...props}
    />
  );
}

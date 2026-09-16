import React from "react";
import { cn } from "../../utils/cn";

export function Container({
  children,
  className = "",
  size = "layout", // "layout" (1400px) or "content" (1200px)
  ...props
}) {
  return (
    <div
      className={cn(
        "w-full mx-auto px-4 sm:px-6 lg:px-8",
        size === "content" ? "max-w-content" : "max-w-layout",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

import React from "react";
import { cn } from "../../utils/cn";

export function Card({
  children,
  className = "",
  hoverable = false,
  elevated = false,
  ...props
}) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border p-5 text-text-primary transition-colors duration-150",
        elevated ? "bg-card-elevated shadow-md shadow-black/40" : "bg-card",
        hoverable && "hover:bg-card-hover hover:border-border-active cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "", ...props }) {
  return (
    <div className={cn("flex flex-col space-y-1.5 pb-3 border-b border-border/60", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = "", ...props }) {
  return (
    <h3 className={cn("text-base font-semibold tracking-tight text-text-primary", className)} {...props}>
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = "", ...props }) {
  return (
    <p className={cn("text-xs text-text-secondary leading-relaxed", className)} {...props}>
      {children}
    </p>
  );
}

export function CardContent({ children, className = "", ...props }) {
  return (
    <div className={cn("pt-4", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = "", ...props }) {
  return (
    <div className={cn("flex items-center pt-4 border-t border-border/60", className)} {...props}>
      {children}
    </div>
  );
}

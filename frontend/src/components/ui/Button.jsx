import React from "react";
import { cn } from "../../utils/cn";
import { Loader2 } from "lucide-react";

export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  disabled = false,
  isLoading = false,
  icon: Icon,
  type = "button",
  onClick,
  ...props
}) {
  const baseStyles =
    "inline-flex items-center justify-center font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer";

  const sizeStyles = {
    sm: "h-8 px-3 text-xs rounded-md gap-1.5",
    md: "h-9 px-4 text-sm rounded-md gap-2",
    lg: "h-11 px-5 text-base rounded-md gap-2.5",
    icon: "h-9 w-9 rounded-md justify-center",
  };

  const variantStyles = {
    primary:
      "bg-primary text-white hover:bg-primary-hover active:bg-primary-active shadow-sm shadow-primary/20",
    secondary:
      "bg-[#181B22] text-text-primary border border-border hover:bg-[#22252D] active:bg-[#14161B]",
    ghost:
      "bg-transparent text-text-secondary hover:bg-card-elevated hover:text-text-primary active:bg-[#14161B]",
    destructive:
      "bg-status-error text-white hover:bg-[#DC2626] active:bg-[#B91C1C] shadow-sm shadow-status-error/20",
    outline:
      "bg-transparent text-text-primary border border-border hover:bg-card-elevated active:bg-[#14161B]",
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin text-current" />
      ) : Icon ? (
        <Icon className="h-4 w-4 shrink-0 text-current" />
      ) : null}
      {children}
    </button>
  );
}

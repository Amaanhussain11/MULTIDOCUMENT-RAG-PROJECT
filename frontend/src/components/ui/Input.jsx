import React from "react";
import { cn } from "../../utils/cn";

export const Input = React.forwardRef(
  ({ className = "", type = "text", error, ...props }, ref) => {
    return (
      <div className="w-full">
        <input
          type={type}
          ref={ref}
          className={cn(
            "w-full h-9 rounded-md bg-card border border-border px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted transition-colors duration-150 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-status-error focus:border-status-error focus:ring-status-error",
            className
          )}
          {...props}
        />
        {error && <p className="mt-1.5 text-xs text-status-error">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";

export const Textarea = React.forwardRef(
  ({ className = "", error, ...props }, ref) => {
    return (
      <div className="w-full">
        <textarea
          ref={ref}
          className={cn(
            "w-full rounded-md bg-card border border-border px-3 py-2 text-sm text-text-primary placeholder:text-text-muted transition-colors duration-150 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50 resize-y",
            error && "border-status-error focus:border-status-error focus:ring-status-error",
            className
          )}
          {...props}
        />
        {error && <p className="mt-1.5 text-xs text-status-error">{error}</p>}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";

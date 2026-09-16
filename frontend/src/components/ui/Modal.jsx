import React, { useEffect, useRef } from "react";
import { cn } from "../../utils/cn";
import { X } from "lucide-react";

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  className = "",
  maxWidth = "max-w-lg",
}) {
  const modalRef = useRef(null);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm transition-opacity duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        ref={modalRef}
        className={cn(
          "w-full rounded-xl bg-card border border-border shadow-2xl shadow-black/80 overflow-hidden transform transition-all duration-200 animate-in fade-in zoom-in-95",
          maxWidth,
          className
        )}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/80">
          <div>
            {title && (
              <h3 id="modal-title" className="text-base font-semibold text-text-primary">
                {title}
              </h3>
            )}
            {description && (
              <p className="mt-0.5 text-xs text-text-secondary">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-text-muted hover:text-text-primary hover:bg-card-elevated transition-colors"
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

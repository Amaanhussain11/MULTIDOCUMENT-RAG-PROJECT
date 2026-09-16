import React from "react";
import { Container } from "./Container";
import { Layers, FileText, MessageSquare, ShieldCheck, Activity } from "lucide-react";
import { cn } from "../../utils/cn";

export function Navbar({ activeTab, onSelectTab, isBackendHealthy = null }) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-md">
      <Container size="layout">
        <div className="flex h-14 items-center justify-between">
          {/* Logo & Product Name */}
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 border border-primary/20 text-primary">
              <Layers className="h-4 w-4" />
            </div>
            <div>
              <span className="text-sm font-semibold tracking-tight text-text-primary">
                Multi-Doc RAG
              </span>
              <span className="hidden sm:inline-block ml-2 text-[11px] font-medium text-text-muted px-1.5 py-0.5 rounded bg-card border border-border">
                v1.0
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 bg-card/60 p-1 rounded-lg border border-border/80">
            <button
              onClick={() => onSelectTab("documents")}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150",
                activeTab === "documents"
                  ? "bg-[#181B22] text-text-primary shadow-sm border border-border"
                  : "text-text-secondary hover:text-text-primary hover:bg-card-hover"
              )}
            >
              <FileText className="h-3.5 w-3.5" />
              Documents
            </button>
            <button
              onClick={() => onSelectTab("chat")}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150",
                activeTab === "chat"
                  ? "bg-[#181B22] text-text-primary shadow-sm border border-border"
                  : "text-text-secondary hover:text-text-primary hover:bg-card-hover"
              )}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Chat
            </button>
          </nav>

          {/* Right Status / Meta */}
          <div className="flex items-center gap-3">
            {/* Backend Health Status indicator */}
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] bg-card border border-border/80 text-text-secondary"
              title={
                isBackendHealthy === true
                  ? "Backend connected (/api/v1/health)"
                  : isBackendHealthy === false
                  ? "Backend offline"
                  : "Checking backend..."
              }
            >
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  isBackendHealthy === true
                    ? "bg-status-success animate-pulse"
                    : isBackendHealthy === false
                    ? "bg-status-error"
                    : "bg-status-warning"
                )}
              />
              <span className="hidden md:inline text-text-muted">API:</span>
              <span className="font-mono text-[10px]">
                {isBackendHealthy === true
                  ? "Active"
                  : isBackendHealthy === false
                  ? "Offline"
                  : "Checking"}
              </span>
            </div>

            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-card-elevated border border-border text-text-muted text-xs font-medium">
              U
            </div>
          </div>
        </div>
      </Container>
    </header>
  );
}

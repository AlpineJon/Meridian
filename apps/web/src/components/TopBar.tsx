"use client";

import { Calendar, ChevronRight, Download, GitCompare } from "lucide-react";
import { cn } from "@/lib/cn";

type Tab = { id: string; label: string };

type Props = {
  geoName: string;
  geoLevel: string;
  geoid: string;
  parentChain: { name: string; geoid: string }[];
  tabs: Tab[];
  activeTab: string;
  onTabChange: (id: string) => void;
};

export function TopBar({ geoName, geoLevel, geoid, parentChain, tabs, activeTab, onTabChange }: Props) {
  return (
    <div className="border-b border-ink-200 bg-white">
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-2 text-[12px]">
          {parentChain.map((p) => (
            <span key={p.geoid} className="flex items-center gap-2 text-ink-500">
              <span>{p.name}</span>
              <ChevronRight className="h-3 w-3 text-ink-300" />
            </span>
          ))}
          <span className="font-semibold text-ink-900">{geoName}</span>
          <span className="ml-1 rounded border border-ink-200 px-1 py-0.5 font-mono text-2xs uppercase text-ink-500">
            {geoLevel}
          </span>
          <span className="ml-1 font-mono text-2xs text-ink-400">{geoid}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="flex items-center gap-1.5 rounded border border-ink-200 bg-white px-2 py-1 text-[12px] text-ink-700 hover:bg-ink-50"
          >
            <Calendar className="h-3.5 w-3.5" />
            Trailing 12 mo
          </button>
          <button
            type="button"
            className="flex items-center gap-1.5 rounded border border-ink-200 bg-white px-2 py-1 text-[12px] text-ink-700 hover:bg-ink-50"
          >
            <GitCompare className="h-3.5 w-3.5" />
            Compare
          </button>
          <button
            type="button"
            className="flex items-center gap-1.5 rounded border border-ink-200 bg-white px-2 py-1 text-[12px] text-ink-700 hover:bg-ink-50"
          >
            <Download className="h-3.5 w-3.5" />
            Export
          </button>
        </div>
      </div>
      <nav className="flex items-center gap-0 border-t border-ink-100 px-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onTabChange(t.id)}
            className={cn(
              "border-b-2 px-3 py-1.5 text-[12px] font-medium transition-colors",
              activeTab === t.id
                ? "border-accent text-accent-700"
                : "border-transparent text-ink-500 hover:text-ink-700",
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

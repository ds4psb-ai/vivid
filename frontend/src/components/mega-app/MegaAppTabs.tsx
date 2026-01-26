"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import type { MegaAppTabsProps } from "./types";

/**
 * MegaAppTabs - Responsive tab navigation
 *
 * Features:
 * - Responsive design (labels hidden on mobile)
 * - NEW badge support
 * - Disabled state support
 * - Custom badge text support
 */
export function MegaAppTabs({ tabs, activeTab, onTabChange }: MegaAppTabsProps) {
  return (
    <div className="flex-shrink-0 border-b bg-white/[0.02] border-white/5">
      <div className="container">
        <Tabs value={activeTab} onValueChange={onTabChange}>
          <TabsList className="h-auto p-1 bg-transparent gap-1">
            {tabs.map((tab) => (
              <TabsTrigger
                key={tab.value}
                value={tab.value}
                disabled={tab.isDisabled}
                className="flex items-center gap-2 px-4 py-2.5 data-[state=active]:bg-white/10 data-[state=active]:text-white text-white/70 hover:text-white/90 transition-colors"
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.isNew && (
                  <Badge
                    variant="secondary"
                    className="ml-1 text-xs bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                  >
                    NEW
                  </Badge>
                )}
                {tab.badge && (
                  <Badge
                    variant="outline"
                    className="ml-1 text-xs border-white/20 text-white/60"
                  >
                    {tab.badge}
                  </Badge>
                )}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>
    </div>
  );
}

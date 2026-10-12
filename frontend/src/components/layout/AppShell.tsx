/**
 * AppShell
 *
 * Shared responsive application layout for Family Context.
 * Updated to match the refined minimalist design system while retaining full family & member selection.
 */

import { useState } from "react";
import { Menu, X, House, Heart, ChevronDown, Users, User } from "lucide-react";

import Navigation from "./Navigation";
import { useFamily } from "../../context/FamilyContext";

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const {
    families,
    selectedFamilyId,
    setSelectedFamilyId,
    members,
    selectedMemberId,
    setSelectedMemberId,
  } = useFamily();

  const activeMembers = members.filter((member) => member.is_active);

  const handleFamilyChange = (familyId: string) => {
    setSelectedFamilyId(familyId);
    setMobileMenuOpen(false);
  };

  const handleMemberChange = (memberId: string) => {
    setSelectedMemberId(memberId || null);
  };

  return (
    <div className="min-h-screen bg-slate-50/50 text-slate-900 font-sans">
      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-200/80 bg-white lg:block">
        <div className="flex h-full flex-col">
          {/* Brand & Selectors */}
          <div className="px-5 pt-6 pb-4">
            <a
              href="/"
              className="group flex items-center gap-3 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-slate-900"
              aria-label="Family Context home"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white transition-colors duration-200">
                <House
                  size={20}
                  strokeWidth={2}
                  aria-hidden="true"
                />
              </span>

              <span className="min-w-0">
                <span className="block text-base font-bold tracking-tight text-slate-900">
                  Family Context
                </span>
                <span className="mt-0.5 block text-[11px] text-slate-500">
                  Your family, in sync
                </span>
              </span>
            </a>

            {/* Selectors */}
            {families.length > 0 && (
              <div className="mt-5 space-y-3">
                {/* Family Selector */}
                <div>
                  <label
                    htmlFor="family-selector"
                    className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400"
                  >
                    <Users size={12} className="text-slate-400" aria-hidden="true" />
                    Family
                  </label>

                  <div className="relative">
                    <select
                      id="family-selector"
                      value={selectedFamilyId ?? ""}
                      onChange={(event) =>
                        handleFamilyChange(event.target.value)
                      }
                      className="w-full appearance-none rounded-xl border border-slate-200 bg-white py-2 pl-3 pr-8 text-xs font-semibold text-slate-900 shadow-xs transition hover:border-slate-300 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                    >
                      {families.map((family) => (
                        <option key={family.id} value={family.id}>
                          {family.name}
                        </option>
                      ))}
                    </select>

                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-slate-400">
                      <ChevronDown size={14} aria-hidden="true" />
                    </div>
                  </div>
                </div>

                {/* Member Selector */}
                {selectedFamilyId && (
                  <div>
                    <label
                      htmlFor="member-selector"
                      className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400"
                    >
                      <User size={12} className="text-slate-400" aria-hidden="true" />
                      Viewing data for
                    </label>

                    <div className="relative">
                      <select
                        id="member-selector"
                        value={selectedMemberId ?? ""}
                        onChange={(event) =>
                          handleMemberChange(event.target.value)
                        }
                        className="w-full appearance-none rounded-xl border border-slate-200 bg-white py-2 pl-3 pr-8 text-xs font-semibold text-slate-900 shadow-xs transition hover:border-slate-300 focus:border-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900/10"
                      >
                        <option value="">All Family</option>

                        {activeMembers.map((member) => (
                          <option key={member.id} value={member.id}>
                            {member.name}
                          </option>
                        ))}
                      </select>

                      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2.5 text-slate-400">
                        <ChevronDown size={14} aria-hidden="true" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex-1 overflow-y-auto px-4 py-1">
            <Navigation />
          </div>

          {/* Sidebar Footer */}
          <div className="p-4">
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200/80 bg-slate-50/60 p-3.5">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white text-slate-800 shadow-xs border border-slate-200/60">
                <Heart size={15} strokeWidth={2} aria-hidden="true" />
              </span>

              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-900">
                  Made for families
                </p>
                <p className="mt-0.5 text-[11px] text-slate-500 truncate">
                  Keep everyone informed and organized.
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur-md lg:hidden">
        <div className="flex min-h-[68px] items-center justify-between px-4 sm:px-6">
          <a
            href="/"
            className="group flex items-center gap-2.5 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-slate-900"
            aria-label="Family Context home"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white">
              <House size={19} strokeWidth={2} aria-hidden="true" />
            </span>

            <span>
              <span className="block text-sm font-bold tracking-tight text-slate-900">
                Family Context
              </span>
              <span className="block text-[10px] text-slate-500">
                Your family, in sync
              </span>
            </span>
          </a>

          <button
            type="button"
            onClick={() => setMobileMenuOpen((open) => !open)}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation"
          >
            {mobileMenuOpen ? (
              <X size={20} aria-hidden="true" />
            ) : (
              <Menu size={20} aria-hidden="true" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div
          id="mobile-navigation"
          className="fixed inset-x-0 bottom-0 top-[68px] z-40 overflow-y-auto border-b border-slate-200 bg-white px-4 py-5 shadow-lg lg:hidden sm:px-6"
        >
          {families.length > 0 && (
            <div className="mb-5 space-y-3">
              <div>
                <label
                  htmlFor="mobile-family-selector"
                  className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400"
                >
                  <Users size={12} className="text-slate-400" aria-hidden="true" />
                  Family
                </label>

                <div className="relative">
                  <select
                    id="mobile-family-selector"
                    value={selectedFamilyId ?? ""}
                    onChange={(event) =>
                      handleFamilyChange(event.target.value)
                    }
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-xs font-semibold text-slate-900 shadow-xs outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                  >
                    {families.map((family) => (
                      <option key={family.id} value={family.id}>
                        {family.name}
                      </option>
                    ))}
                  </select>

                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400">
                    <ChevronDown size={15} aria-hidden="true" />
                  </div>
                </div>
              </div>

              {selectedFamilyId && (
                <div>
                  <label
                    htmlFor="mobile-member-selector"
                    className="mb-1.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-400"
                  >
                    <User size={12} className="text-slate-400" aria-hidden="true" />
                    Viewing data for
                  </label>

                  <div className="relative">
                    <select
                      id="mobile-member-selector"
                      value={selectedMemberId ?? ""}
                      onChange={(event) =>
                        handleMemberChange(event.target.value)
                      }
                      className="w-full appearance-none rounded-xl border border-slate-200 bg-white py-2.5 pl-3 pr-9 text-xs font-semibold text-slate-900 shadow-xs outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                    >
                      <option value="">All Family</option>

                      {activeMembers.map((member) => (
                        <option key={member.id} value={member.id}>
                          {member.name}
                        </option>
                      ))}
                    </select>

                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400">
                      <ChevronDown size={15} aria-hidden="true" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          <Navigation />

          <button
            type="button"
            onClick={() => setMobileMenuOpen(false)}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50"
          >
            <X size={15} aria-hidden="true" />
            Close menu
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="min-h-screen lg:ml-64">
        <div className="mx-auto w-full max-w-[1600px] px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
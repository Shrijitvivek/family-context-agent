/**
 * AppShell
 *
 * Shared responsive application layout for Family Context.
 *
 * Features:
 * - Branded home logo.
 * - Desktop sidebar navigation.
 * - Responsive mobile navigation.
 * - Family and member selection for desktop and mobile with elevated custom select design.
 * - Consistent page spacing and styling.
 * - Accessible navigation controls.
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
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Desktop Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-200/80 bg-white lg:block">
        <div className="flex h-full flex-col">
          {/* Brand */}
          <div className="border-b border-slate-100 px-5 py-5">
            <a
              href="/"
              className="group flex items-center gap-3 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
              aria-label="Family Context home"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-violet-100 bg-violet-50 text-violet-700 transition-colors duration-200 group-hover:bg-violet-100">
                <House
                  size={23}
                  strokeWidth={2}
                  aria-hidden="true"
                />
              </span>

              <span className="min-w-0">
                <span className="block text-[17px] font-bold tracking-tight text-slate-900">
                  Family Context
                </span>

                <span className="mt-0.5 block text-xs text-slate-500">
                  Your family, in sync
                </span>
              </span>
            </a>

            {/* Selectors */}
            {families.length > 0 && (
              <div className="mt-6 space-y-4">
                {/* Family Selector */}
                <div>
                  <label
                    htmlFor="family-selector"
                    className="mb-1.5 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-slate-400"
                  >
                    <span className="flex items-center gap-1.5">
                      <Users size={12} className="text-slate-400" aria-hidden="true" />
                      Current family
                    </span>
                  </label>

                  <div className="relative">
                    <select
                      id="family-selector"
                      value={selectedFamilyId ?? ""}
                      onChange={(event) =>
                        handleFamilyChange(event.target.value)
                      }
                      className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50/80 py-2.5 pl-3.5 pr-9 text-sm font-medium text-slate-800 shadow-xs transition hover:border-slate-300 hover:bg-white focus:border-violet-400 focus:bg-white focus:outline-none focus:ring-3 focus:ring-violet-100/80"
                    >
                      {families.map((family) => (
                        <option key={family.id} value={family.id}>
                          {family.name}
                        </option>
                      ))}
                    </select>

                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400">
                      <ChevronDown size={16} aria-hidden="true" />
                    </div>
                  </div>
                </div>

                {/* Member Selector */}
                {selectedFamilyId && (
                  <div>
                    <label
                      htmlFor="member-selector"
                      className="mb-1.5 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-slate-400"
                    >
                      <span className="flex items-center gap-1.5">
                        <User size={12} className="text-slate-400" aria-hidden="true" />
                        Viewing data for
                      </span>
                    </label>

                    <div className="relative">
                      <select
                        id="member-selector"
                        value={selectedMemberId ?? ""}
                        onChange={(event) =>
                          handleMemberChange(event.target.value)
                        }
                        className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50/80 py-2.5 pl-3.5 pr-9 text-sm font-medium text-slate-800 shadow-xs transition hover:border-slate-300 hover:bg-white focus:border-violet-400 focus:bg-white focus:outline-none focus:ring-3 focus:ring-violet-100/80"
                      >
                        <option value="">All Family</option>

                        {activeMembers.map((member) => (
                          <option key={member.id} value={member.id}>
                            {member.name}
                          </option>
                        ))}
                      </select>

                      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400">
                        <ChevronDown size={16} aria-hidden="true" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <Navigation />
          </div>

          {/* Sidebar Footer */}
          <div className="border-t border-slate-100 p-4">
            <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-3 py-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-violet-600 ring-1 ring-slate-200/80">
                <Heart size={17} strokeWidth={1.9} aria-hidden="true" />
              </span>

              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-700">
                  Made for families
                </p>
                <p className="mt-0.5 text-[11px] text-slate-500">
                  Everything connected.
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur-md lg:hidden">
        <div className="flex min-h-[68px] items-center justify-between px-4 sm:px-6">
          {/* Mobile Brand */}
          <a
            href="/"
            className="group flex items-center gap-2.5 rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
            aria-label="Family Context home"
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-violet-100 bg-violet-50 text-violet-700 transition-colors group-hover:bg-violet-100">
              <House
                size={21}
                strokeWidth={2}
                aria-hidden="true"
              />
            </span>

            <span>
              <span className="block text-base font-bold tracking-tight text-slate-900">
                Family Context
              </span>
              <span className="block text-[11px] text-slate-500">
                Your family, in sync
              </span>
            </span>
          </a>

          {/* Menu Toggle */}
          <button
            type="button"
            onClick={() =>
              setMobileMenuOpen((open) => !open)
            }
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
            aria-label={
              mobileMenuOpen ? "Close menu" : "Open menu"
            }
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation"
          >
            {mobileMenuOpen ? (
              <X size={21} aria-hidden="true" />
            ) : (
              <Menu size={21} aria-hidden="true" />
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
          {/* Mobile Selectors */}
          {families.length > 0 && (
            <div className="mb-6 space-y-4">
              {/* Mobile Family Selector */}
              <div>
                <label
                  htmlFor="mobile-family-selector"
                  className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400"
                >
                  <Users size={12} className="text-slate-400" aria-hidden="true" />
                  Current family
                </label>

                <div className="relative">
                  <select
                    id="mobile-family-selector"
                    value={selectedFamilyId ?? ""}
                    onChange={(event) =>
                      handleFamilyChange(event.target.value)
                    }
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50 py-3 pl-3.5 pr-10 text-sm font-medium text-slate-800 shadow-xs outline-none transition focus:border-violet-400 focus:bg-white focus:ring-3 focus:ring-violet-100"
                  >
                    {families.map((family) => (
                      <option key={family.id} value={family.id}>
                        {family.name}
                      </option>
                    ))}
                  </select>

                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400">
                    <ChevronDown size={18} aria-hidden="true" />
                  </div>
                </div>
              </div>

              {/* Mobile Member Selector */}
              {selectedFamilyId && (
                <div>
                  <label
                    htmlFor="mobile-member-selector"
                    className="mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400"
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
                      className="w-full appearance-none rounded-xl border border-slate-200 bg-slate-50 py-3 pl-3.5 pr-10 text-sm font-medium text-slate-800 shadow-xs outline-none transition focus:border-violet-400 focus:bg-white focus:ring-3 focus:ring-violet-100"
                    >
                      <option value="">All Family</option>

                      {activeMembers.map((member) => (
                        <option key={member.id} value={member.id}>
                          {member.name}
                        </option>
                      ))}
                    </select>

                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400">
                      <ChevronDown size={18} aria-hidden="true" />
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
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
          >
            <X size={16} aria-hidden="true" />
            Close menu
          </button>
        </div>
      )}

      {/* Main Content */}
      <main className="min-h-screen lg:ml-64">
        <div className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
'use client';

import React, { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { PersonaCard } from '@/components/PersonaCard';
import { EmptyState } from '@/components/EmptyState';
import { Users, Search, Filter, ArrowUpDown, Sparkles } from 'lucide-react';

export default function PersonaLabPage() {
  const router = useRouter();
  const { personas, experiment } = useAppStore();
  const [search, setSearch] = useState('');
  const [techFilter, setTechFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'score' | 'age' | 'name'>('score');

  const filteredPersonas = useMemo(() => {
    return personas
      .filter((p) => {
        const matchesSearch =
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          p.occupation.toLowerCase().includes(search.toLowerCase()) ||
          p.bio.toLowerCase().includes(search.toLowerCase()) ||
          (p.goals || []).some((g) => g.toLowerCase().includes(search.toLowerCase()));

        const matchesTech =
          techFilter === 'all' ||
          (p.technology_usage && p.technology_usage.toLowerCase().includes(techFilter.toLowerCase()));

        return matchesSearch && matchesTech;
      })
      .sort((a, b) => {
        if (sortBy === 'score') return (b.quality_score || 0) - (a.quality_score || 0);
        if (sortBy === 'age') return a.age - b.age;
        return a.name.localeCompare(b.name);
      });
  }, [personas, search, techFilter, sortBy]);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Persona Lab"
        subtitle={`Inspect demographic, psychological, and behavioral attributes for ${personas.length} active personas.`}
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {personas.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No Personas Generated Yet"
            description="Start by defining your target audience and research objective in the Workspace to synthesize synthetic personas."
            actionHref="/"
            actionLabel="Go to Workspace"
          />
        ) : (
          <>
            {/* Search & Filter Controls */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 items-center justify-between">
              {/* Search Bar */}
              <div className="relative w-full md:w-80">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by name, role, goal, or bio..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                />
              </div>

              {/* Filters & Sorting */}
              <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                <div className="flex items-center gap-1.5 text-xs text-slate-600">
                  <Filter className="w-3.5 h-3.5 text-slate-400" />
                  <span className="font-semibold">Tech:</span>
                  <select
                    value={techFilter}
                    onChange={(e) => setTechFilter(e.target.value)}
                    className="px-2 py-1.5 rounded-lg border border-slate-200 text-xs bg-white focus:outline-none focus:border-teal-500"
                  >
                    <option value="all">All Levels</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                <div className="flex items-center gap-1.5 text-xs text-slate-600">
                  <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
                  <span className="font-semibold">Sort:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="px-2 py-1.5 rounded-lg border border-slate-200 text-xs bg-white focus:outline-none focus:border-teal-500"
                  >
                    <option value="score">Quality Score</option>
                    <option value="age">Age</option>
                    <option value="name">Name</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Persona Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredPersonas.map((persona, index) => (
                <PersonaCard
                  key={index}
                  persona={persona}
                  onInterviewClick={() => router.push(`/interview?persona=${encodeURIComponent(persona.name)}`)}
                />
              ))}
            </div>

            {filteredPersonas.length === 0 && (
              <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-500 text-xs">
                No personas match the current search filter.
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import { Persona } from '@/lib/types';
import { StatusBadge } from './StatusBadge';
import {
  User,
  Briefcase,
  GraduationCap,
  DollarSign,
  MapPin,
  ChevronDown,
  ChevronUp,
  Cpu,
  ShoppingCart,
  BrainCircuit,
  Activity,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

interface PersonaCardProps {
  persona: Persona;
  onInterviewClick?: () => void;
}

export const PersonaCard: React.FC<PersonaCardProps> = ({ persona, onInterviewClick }) => {
  const [expanded, setExpanded] = useState(false);

  const bigFive = persona.big_five_personality;
  const psych = persona.psychological_profile;
  const behavior = persona.behavior_pattern;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-teal-100 text-teal-800 font-bold text-lg flex items-center justify-center border border-teal-200">
              {persona.name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-slate-900 text-base">{persona.name}</h3>
                <span className="text-xs text-slate-500 font-medium">({persona.age} y/o • {persona.gender})</span>
              </div>
              <p className="text-xs text-teal-700 font-medium mt-0.5">{persona.occupation}</p>
            </div>
          </div>

          <div className="text-right">
            <div className="flex items-center gap-1.5 justify-end">
              <span className="text-xs font-bold text-slate-700">Quality:</span>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200">
                {persona.quality_score || 92}/100
              </span>
            </div>
            <div className="mt-1">
              <StatusBadge status={persona.quality_status || 'Verified Cohort'} size="sm" />
            </div>
          </div>
        </div>

        {/* Quick Demographics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-600">
          <div className="flex items-center gap-1.5">
            <GraduationCap className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate">{persona.education || 'Graduate'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate">{persona.income || '$75k/yr'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate">{persona.location || 'Metro Area'}</span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-5 space-y-4 text-xs">
        {/* Bio */}
        <div>
          <h4 className="font-semibold text-slate-900 mb-1 text-[11px] uppercase tracking-wider text-slate-500">Bio</h4>
          <p className="text-slate-600 leading-relaxed">{persona.bio}</p>
        </div>

        {/* Goals & Pain Points */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-emerald-50/50 p-3 rounded-lg border border-emerald-100">
            <h4 className="font-semibold text-emerald-900 mb-1.5 flex items-center gap-1.5 text-xs">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Core Goals
            </h4>
            <ul className="space-y-1 text-emerald-800 text-[11px]">
              {(persona.goals || []).map((goal, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-emerald-500 font-bold">•</span>
                  <span>{goal}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-rose-50/50 p-3 rounded-lg border border-rose-100">
            <h4 className="font-semibold text-rose-900 mb-1.5 flex items-center gap-1.5 text-xs">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
              Pain Points
            </h4>
            <ul className="space-y-1 text-rose-800 text-[11px]">
              {(persona.pain_points || []).map((pain, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="text-rose-500 font-bold">•</span>
                  <span>{pain}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Tech & Buying */}
        <div className="grid grid-cols-2 gap-3 pt-2">
          <div className="flex items-start gap-2">
            <Cpu className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-700 block text-[11px]">Tech Usage</span>
              <span className="text-slate-600 text-[11px]">{persona.technology_usage}</span>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <ShoppingCart className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-700 block text-[11px]">Buying Behavior</span>
              <span className="text-slate-600 text-[11px]">{persona.buying_behavior}</span>
            </div>
          </div>
        </div>

        {/* Expandable Psychological & Big Five Profile */}
        {expanded && (
          <div className="pt-4 border-t border-slate-100 space-y-4 animate-in fade-in duration-200">
            {/* Psychological & Behavioral */}
            <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-800 flex items-center gap-1.5 text-xs">
                <BrainCircuit className="w-3.5 h-3.5 text-teal-600" />
                Psychological & Behavioral Pattern
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-600">
                {psych?.motivation && <div><span className="font-semibold text-slate-700">Motivation:</span> {psych.motivation}</div>}
                {psych?.decision_style && <div><span className="font-semibold text-slate-700">Decision:</span> {psych.decision_style}</div>}
                {psych?.risk_tolerance && <div><span className="font-semibold text-slate-700">Risk Tolerance:</span> {psych.risk_tolerance}</div>}
                {behavior?.shopping && <div><span className="font-semibold text-slate-700">Shopping Style:</span> {behavior.shopping}</div>}
              </div>
            </div>

            {/* Big Five */}
            {bigFive && (
              <div className="space-y-2">
                <h4 className="font-bold text-slate-800 flex items-center gap-1.5 text-xs">
                  <Activity className="w-3.5 h-3.5 text-teal-600" />
                  Big Five Personality Traits
                </h4>
                <div className="space-y-1.5">
                  {Object.entries(bigFive).map(([trait, score]) => (
                    <div key={trait} className="flex items-center gap-3 text-[11px]">
                      <span className="w-28 capitalize text-slate-600 font-medium">{trait}</span>
                      <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
                        <div
                          className="bg-teal-500 h-full rounded-full"
                          style={{ width: `${Number(score)}%` }}
                        />
                      </div>
                      <span className="w-8 text-right font-semibold text-slate-700">{score}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-slate-600 hover:text-slate-900 font-medium flex items-center gap-1"
        >
          {expanded ? (
            <>
              <span>Less details</span>
              <ChevronUp className="w-3.5 h-3.5" />
            </>
          ) : (
            <>
              <span>Full psychological breakdown</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </>
          )}
        </button>

        {onInterviewClick && (
          <button
            onClick={onInterviewClick}
            className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition"
          >
            Start Interview
          </button>
        )}
      </div>
    </div>
  );
};

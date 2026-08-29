'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  Experiment,
  Persona,
  SurveyResult,
  InterviewMemory,
  FocusGroupTurn,
  InsightsData,
  ProductDecision,
  SimulationResult,
  ConsultantReport
} from './types';

interface AppContextType {
  experiment: Experiment;
  setExperiment: React.Dispatch<React.SetStateAction<Experiment>>;
  personas: Persona[];
  setPersonas: React.Dispatch<React.SetStateAction<Persona[]>>;
  surveyResult: SurveyResult | null;
  setSurveyResult: React.Dispatch<React.SetStateAction<SurveyResult | null>>;
  interviewMemories: Record<string, InterviewMemory>;
  setInterviewMemories: React.Dispatch<React.SetStateAction<Record<string, InterviewMemory>>>;
  focusGroupTranscript: FocusGroupTurn[];
  setFocusGroupTranscript: React.Dispatch<React.SetStateAction<FocusGroupTurn[]>>;
  insights: InsightsData | null;
  setInsights: React.Dispatch<React.SetStateAction<InsightsData | null>>;
  actions: ProductDecision[];
  setActions: React.Dispatch<React.SetStateAction<ProductDecision[]>>;
  simulationResult: SimulationResult | null;
  setSimulationResult: React.Dispatch<React.SetStateAction<SimulationResult | null>>;
  report: { markdown: string; consultant_report?: ConsultantReport } | null;
  setReport: React.Dispatch<React.SetStateAction<{ markdown: string; consultant_report?: ConsultantReport } | null>>;
  loadDemoData: () => void;
  resetAll: () => void;
  isDemoMode: boolean;
}

const defaultExperiment: Experiment = {
  experiment_name: 'SaaS Productivity Validation',
  product_name: 'TaskFlow AI',
  description: 'AI-powered workflow automation and meeting intelligence tool designed for fast-moving engineering and product teams.',
  target_audience: 'Software Engineers, Engineering Managers, Product Managers',
  research_objective: 'Evaluate pricing sensitivity, adoption blockers, and trial conversion rates.',
  industry: 'Enterprise Software / SaaS',
  simulation_type: 'Product Adoption & Pricing',
  persona_count: 4,
  age: '24-45',
  gender: 'Diverse Cohort',
  profession: 'Technology & Product Management',
  location: 'Global / Remote',
  interests: 'Productivity, AI Workflows, Agile, Developer Tools',
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [experiment, setExperiment] = useState<Experiment>(defaultExperiment);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [surveyResult, setSurveyResult] = useState<SurveyResult | null>(null);
  const [interviewMemories, setInterviewMemories] = useState<Record<string, InterviewMemory>>({});
  const [focusGroupTranscript, setFocusGroupTranscript] = useState<FocusGroupTurn[]>([]);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [actions, setActions] = useState<ProductDecision[]>([]);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [report, setReport] = useState<{ markdown: string; consultant_report?: ConsultantReport } | null>(null);
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false);

  // Initialize from localStorage
  useEffect(() => {
    try {
      const savedExp = localStorage.getItem('ai_studio_exp');
      if (savedExp) setExperiment(JSON.parse(savedExp));

      const savedPersonas = localStorage.getItem('ai_studio_personas');
      if (savedPersonas) setPersonas(JSON.parse(savedPersonas));

      const savedSurvey = localStorage.getItem('ai_studio_survey');
      if (savedSurvey) setSurveyResult(JSON.parse(savedSurvey));

      const savedInsights = localStorage.getItem('ai_studio_insights');
      if (savedInsights) setInsights(JSON.parse(savedInsights));

      const savedActions = localStorage.getItem('ai_studio_actions');
      if (savedActions) setActions(JSON.parse(savedActions));
    } catch (e) {
      console.warn('Could not read from localStorage', e);
    }
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem('ai_studio_exp', JSON.stringify(experiment));
      localStorage.setItem('ai_studio_personas', JSON.stringify(personas));
      if (surveyResult) localStorage.setItem('ai_studio_survey', JSON.stringify(surveyResult));
      if (insights) localStorage.setItem('ai_studio_insights', JSON.stringify(insights));
      if (actions.length) localStorage.setItem('ai_studio_actions', JSON.stringify(actions));
    } catch (e) {
      // Ignore storage errors
    }
  }, [experiment, personas, surveyResult, insights, actions]);

  const loadDemoData = () => {
    setIsDemoMode(true);
    setExperiment(defaultExperiment);
    // Trigger real mock set if user requests Demo Mode
  };

  const resetAll = () => {
    setExperiment(defaultExperiment);
    setPersonas([]);
    setSurveyResult(null);
    setInterviewMemories({});
    setFocusGroupTranscript([]);
    setInsights(null);
    setActions([]);
    setSimulationResult(null);
    setReport(null);
    setIsDemoMode(false);
    try {
      localStorage.clear();
    } catch (e) {}
  };

  return (
    <AppContext.Provider
      value={{
        experiment,
        setExperiment,
        personas,
        setPersonas,
        surveyResult,
        setSurveyResult,
        interviewMemories,
        setInterviewMemories,
        focusGroupTranscript,
        setFocusGroupTranscript,
        insights,
        setInsights,
        actions,
        setActions,
        simulationResult,
        setSimulationResult,
        report,
        setReport,
        loadDemoData,
        resetAll,
        isDemoMode,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppStore = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppStore must be used within an AppProvider');
  return context;
};

import {
  Experiment,
  Persona,
  SurveyResult,
  InterviewMemory,
  InterviewMessage,
  FocusGroupTurn,
  InsightsData,
  ProductDecision,
  SimulationResult,
  ConsultantReport
} from './types';

const API_BASE = '/api';

export async function checkHealth(): Promise<{ status: string; engine: string; gemini_configured: boolean }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchSurveyTemplates(): Promise<{ templates: string[]; details: Record<string, any> }> {
  const res = await fetch(`${API_BASE}/templates`);
  if (!res.ok) throw new Error('Failed to fetch templates');
  return res.json();
}

export async function generatePersonasAPI(experiment: Partial<Experiment>): Promise<{
  personas: Persona[];
  persona_count: number;
  source: string;
  population_diversity?: any;
  last_error?: string;
}> {
  const res = await fetch(`${API_BASE}/personas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(experiment),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to generate personas' }));
    throw new Error(err.detail || 'Failed to generate personas');
  }
  return res.json();
}

export async function runSurveyAPI(params: {
  personas: Persona[];
  product_name: string;
  research_goal: string;
  template?: string;
  custom_questions?: any[];
}): Promise<SurveyResult> {
  const res = await fetch(`${API_BASE}/survey`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to execute survey' }));
    throw new Error(err.detail || 'Failed to execute survey');
  }
  return res.json();
}

export async function sendInterviewMessageAPI(params: {
  persona: Persona;
  question: string;
  memory_payload?: InterviewMemory | null;
  experiment?: Partial<Experiment>;
}): Promise<{
  reply: string;
  memory: InterviewMemory;
  quote: string;
  sentiment: string;
  emotional_state: string;
  follow_up_questions: string[];
}> {
  const res = await fetch(`${API_BASE}/interview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to communicate with persona' }));
    throw new Error(err.detail || 'Failed to communicate with persona');
  }
  return res.json();
}

export async function runFocusGroupAPI(params: {
  question: string;
  personas: Persona[];
  experiment?: Partial<Experiment>;
}): Promise<{ transcript: FocusGroupTurn[] }> {
  const res = await fetch(`${API_BASE}/focus-group`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to run focus group' }));
    throw new Error(err.detail || 'Failed to run focus group');
  }
  return res.json();
}

export async function fetchInsightsAPI(params: {
  personas: Persona[];
  survey_results?: SurveyResult | null;
  interview_results?: InterviewMessage[];
  focus_group_results?: FocusGroupTurn[];
  experiment?: Partial<Experiment>;
}): Promise<InsightsData> {
  const res = await fetch(`${API_BASE}/insights`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to generate insights' }));
    throw new Error(err.detail || 'Failed to generate insights');
  }
  return res.json();
}

export async function fetchActionsAPI(params: {
  experiment?: Partial<Experiment>;
  personas: Persona[];
  insights?: InsightsData | null;
  survey_results?: SurveyResult | null;
}): Promise<{ actions: ProductDecision[] }> {
  const res = await fetch(`${API_BASE}/actions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to generate actions' }));
    throw new Error(err.detail || 'Failed to generate actions');
  }
  return res.json();
}

export async function runSimulationAPI(params: {
  baseline_fit: number;
  pricing_strategy?: string;
  trust_signals?: boolean;
  onboarding_friction_reduction?: number;
  automation_added?: boolean;
  trial_bonus?: number;
  guarantee_offered?: boolean;
}): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/simulation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to run simulation' }));
    throw new Error(err.detail || 'Failed to run simulation');
  }
  return res.json();
}

export async function fetchReportsAPI(params: {
  experiment?: Partial<Experiment>;
  personas: Persona[];
  survey_results?: SurveyResult | null;
  interview_rows?: InterviewMessage[];
  insights?: InsightsData | null;
  focus_group?: FocusGroupTurn[];
}): Promise<{
  markdown: string;
  consultant_report: ConsultantReport;
  generated_at?: string;
}> {
  const res = await fetch(`${API_BASE}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to generate report' }));
    throw new Error(err.detail || 'Failed to generate report');
  }
  return res.json();
}

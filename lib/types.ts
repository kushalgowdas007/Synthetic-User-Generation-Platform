export interface Persona {
  id?: string;
  name: string;
  age: number;
  gender: string;
  occupation: string;
  education: string;
  income: string;
  company?: string;
  location?: string;
  bio: string;
  goals: string[];
  pain_points: string[];
  technology_usage: string;
  buying_behavior: string;
  psychological_profile?: {
    motivation?: string;
    values?: string;
    decision_style?: string;
    risk_tolerance?: string;
    emotional_traits?: string;
  };
  behavior_pattern?: {
    shopping?: string;
    communication?: string;
    social_media?: string;
    daily_routine?: string;
    brand_loyalty?: string;
  };
  big_five_personality?: {
    openness?: number;
    conscientiousness?: number;
    extraversion?: number;
    agreeableness?: number;
    neuroticism?: number;
  };
  quality_score?: number;
  needs_review?: boolean;
  quality_warnings?: string[];
  quality_status?: string;
}

export interface Experiment {
  experiment_name: string;
  product_name: string;
  description: string;
  target_audience: string;
  research_objective: string;
  industry: string;
  simulation_type: string;
  persona_count: number;
  age: string;
  gender: string;
  profession: string;
  location: string;
  interests: string;
}

export interface SurveyResponse {
  persona_name: string;
  question: string;
  category: string;
  answer: string;
  reasoning: string;
  score: number;
  sentiment: string;
  hesitation_flag: boolean;
}

export interface SurveyResult {
  responses: SurveyResponse[];
  product_fit_score: number;
  category_breakdown?: Record<string, { avg_score: number; response_count: number }>;
  adoption_barriers?: string[];
  summary?: string;
}

export interface InterviewMessage {
  role: 'user' | 'persona';
  message: string;
  topic?: string;
  emotional_state?: string;
  timestamp?: string;
}

export interface InterviewMemory {
  persona_id: string;
  persona_name: string;
  history: InterviewMessage[];
  opinions: Record<string, string>;
  conversation_summary: string;
  emotional_state: string;
  follow_up_questions: string[];
  consistency_score: number;
  contradictions: string[];
  warnings?: string[];
}

export interface FocusGroupTurn {
  speaker: string;
  role: string;
  message: string;
}

export interface EvidencePoint {
  source_type: string;
  source_detail: string;
  metric_or_quote: string;
  affected_personas: string[];
  confidence: number;
}

export interface StructuredInsight {
  title: string;
  type: string;
  severity_or_importance: number;
  confidence: number;
  affected_personas_count: number;
  affected_personas: string[];
  evidence: EvidencePoint[];
  source: string[];
  recommendation: string;
}

export interface InsightsData {
  themes?: Array<{ theme: string; count: number; confidence_score: number }>;
  pain_points?: Array<{ pain_point: string; count: number; confidence_score: number }>;
  product_adoption_barriers?: Array<{ barrier: string; count: number; confidence_score: number }>;
  positive_signals?: Array<{ signal: string; count: number; confidence_score: number }>;
  feature_requests?: Array<{ feature: string; count: number; confidence_score: number }>;
  sentiment?: string;
  sentiment_distribution?: Record<string, { count: number; confidence_score: number }>;
  product_fit_score?: number;
  recommendation_score?: number;
  early_adopter_detection?: Array<{ persona_name: string; occupation: string; score: number; why: string }>;
  structured_insights?: StructuredInsight[];
  recommendations?: string[];
  final_ai_recommendations?: Array<{ recommendation: string; confidence_score: number }>;
  executive_summary?: string;
  risk_analysis?: string[];
  confidence_score?: number;
}

export interface ProductDecision {
  id: string;
  title: string;
  problem: string;
  recommendation: string;
  priority: number;
  impact: number;
  effort: number;
  confidence: number;
  evidence_strength: number;
  urgency: number;
  affected_personas: string[];
  expected_outcomes: string[];
  source_insights: string[];
  status: 'Recommended' | 'Planned' | 'In Progress' | 'Completed' | 'Rejected';
  breakdown?: {
    impact: number;
    confidence: number;
    evidence_strength: number;
    urgency: number;
    effort: number;
    formula_explanation: string;
  };
}

export interface SimulationResult {
  label: string;
  disclaimer: string;
  baseline_fit: number;
  simulated_fit: number;
  delta: number;
  predicted_adoption_rate: number;
  factors: Array<{ factor: string; impact: string }>;
}

export interface ConsultantReport {
  launch_readiness: number;
  market_fit: number;
  revenue_potential: string;
  risk_score: number;
  pricing_recommendation: string;
  customer_segment: string;
  feature_priorities: string[];
  business_recommendations: string[];
  roadmap: string[];
  swot: {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
    threats: string[];
  };
  why: string;
  decisions: ProductDecision[];
  top_decisions: ProductDecision[];
}

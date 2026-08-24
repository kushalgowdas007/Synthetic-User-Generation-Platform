from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class PersonaQualityScore(BaseModel):
    overall_score: int = Field(default=85, ge=0, le=100)
    realism: int = Field(default=85, ge=0, le=100)
    coherence: int = Field(default=85, ge=0, le=100)
    completeness: int = Field(default=85, ge=0, le=100)
    diversity: int = Field(default=85, ge=0, le=100)
    behavioral_consistency: int = Field(default=85, ge=0, le=100)
    research_usefulness: int = Field(default=85, ge=0, le=100)
    needs_review: bool = False
    warnings: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PopulationDiversityReport(BaseModel):
    diversity_score: int = Field(default=80, ge=0, le=100)
    age_distribution: Dict[str, int] = Field(default_factory=dict)
    gender_distribution: Dict[str, int] = Field(default_factory=dict)
    occupation_distribution: Dict[str, int] = Field(default_factory=dict)
    technology_distribution: Dict[str, int] = Field(default_factory=dict)
    buying_behavior_distribution: Dict[str, int] = Field(default_factory=dict)
    is_low_diversity: bool = False
    diversity_warnings: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ContradictionItem(BaseModel):
    turn_user: str
    turn_assistant: str
    topic: str
    contradiction: str
    severity: str = "Medium"  # Low, Medium, High, Critical


class InterviewConsistencyReport(BaseModel):
    consistency_score: int = Field(default=90, ge=0, le=100)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    supporting_turns: List[Dict[str, str]] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class InsightEvidence(BaseModel):
    source_type: str  # survey, interview, focus_group
    source_ref: str  # Question ID, transcript turn, metric name
    detail: str
    sample_size: int = 1
    confidence: int = 80


class StructuredInsight(BaseModel):
    id: str
    title: str
    type: str  # Theme, Pain Point, Opportunity, Contradiction, Risk, Positive Signal, Behavioral Pattern, Segment Difference
    severity: int = Field(default=50, ge=0, le=100)
    confidence: int = Field(default=80, ge=0, le=100)
    affected_personas_count: int = 0
    affected_personas: List[str] = Field(default_factory=list)
    evidence: List[InsightEvidence] = Field(default_factory=list)
    evidence_text: str = "Insufficient quantitative evidence"
    sources: List[str] = Field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ProductAction(BaseModel):
    id: str
    title: str
    problem: str
    recommendation: str
    priority: int = Field(default=50, ge=0, le=100)
    impact: int = Field(default=50, ge=0, le=100)
    effort: int = Field(default=50, ge=0, le=100)
    confidence: int = Field(default=80, ge=0, le=100)
    evidence_strength: int = Field(default=80, ge=0, le=100)
    affected_users_score: int = Field(default=50, ge=0, le=100)
    urgency: int = Field(default=50, ge=0, le=100)
    affected_personas: List[str] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)
    source_insights: List[str] = Field(default_factory=list)
    status: str = "Recommended"

    def priority_breakdown(self) -> Dict[str, int]:
        return {
            "Impact": self.impact,
            "Confidence": self.confidence,
            "Evidence Strength": self.evidence_strength,
            "Affected Users": self.affected_users_score,
            "Urgency": self.urgency,
            "Effort": self.effort,
        }

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["priority_breakdown"] = self.priority_breakdown()
        return data


class ExperimentSignature(BaseModel):
    hash_value: str
    normalized_input: Dict[str, Any]

    @classmethod
    def create(cls, data: Dict[str, Any]) -> ExperimentSignature:
        sorted_json = json.dumps(data, sort_keys=True, default=str)
        hash_val = hashlib.sha256(sorted_json.encode("utf-8")).hexdigest()
        return cls(hash_value=hash_val, normalized_input=data)

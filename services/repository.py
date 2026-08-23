from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional

from services.workspace_store import list_workspaces, load_workspace, save_workspace


class WorkspaceRepository(abc.ABC):
    """Abstract persistence repository for research workspaces and experiment artifacts."""

    @abc.abstractmethod
    def save(self, workspace_data: Dict[str, Any]) -> str:
        """Save workspace data and return the workspace ID."""
        pass

    @abc.abstractmethod
    def load(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Load workspace data by ID."""
        pass

    @abc.abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """List summary records of all stored workspaces."""
        pass


class JsonWorkspaceRepository(WorkspaceRepository):
    """Local JSON-backed workspace repository (default persistence implementation)."""

    def save(self, workspace_data: Dict[str, Any]) -> str:
        record = save_workspace(
            experiment=workspace_data.get("experiment", {}),
            personas=workspace_data.get("personas", []),
            survey_results=workspace_data.get("survey_results"),
            interview_results=workspace_data.get("interview_results", []),
            insights=workspace_data.get("insights"),
            persona_memories=workspace_data.get("persona_memories", {}),
            research_plan=workspace_data.get("research_plan") or {},
            focus_group_results=workspace_data.get("focus_group_results", []),
            consultant_report=workspace_data.get("consultant_report") or {},
        )
        return str(record.get("id", ""))

    def load(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        return load_workspace(workspace_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return list_workspaces()


# Default singleton instance
default_repository: WorkspaceRepository = JsonWorkspaceRepository()

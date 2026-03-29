from __future__ import annotations

from dataclasses import dataclass

from app.services.analysis_service import AnalysisService
from app.services.document_parser import DocumentParserService
from app.services.github_service import GitHubSearchService
from app.services.installer_service import InstallerService
from app.services.merge_service import MergeService
from app.services.orchestrator_service import OrchestratorService
from app.services.report_service import ReportService
from app.services.retrieval_service import RetrievalService
from app.services.vector_store import VectorStore


@dataclass(slots=True)
class ServiceContainer:
    parser: DocumentParserService
    vector_store: VectorStore
    retrieval: RetrievalService
    report: ReportService
    analysis: AnalysisService
    merge: MergeService
    github: GitHubSearchService
    installer: InstallerService
    orchestrator: OrchestratorService

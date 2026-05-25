"""
Semantic search and analysis API routes.

Phase 6: Semantic Logging Integration
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from forge.db.postgres import PostgresDB
from forge.semantic.embeddings import EmbeddingEngine
from forge.semantic.processor import SemanticProcessor
from forge.semantic.summary import SummaryGenerator

router = APIRouter(prefix="/api/v1", tags=["semantic"])

# Global instances (initialized in main.py)
_db: PostgresDB = None
_processor: SemanticProcessor = None
_summary_generator: SummaryGenerator = None


def init_semantic(db: PostgresDB, processor: SemanticProcessor, summary_gen: Optional[SummaryGenerator] = None):
    """Initialize semantic routes with database and processor."""
    global _db, _processor, _summary_generator
    _db = db
    _processor = processor
    _summary_generator = summary_gen


@router.get("/experiments/{experiment_id}/semantic-search")
async def semantic_search(
    experiment_id: str,
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(10, ge=1, le=100),
):
    """Search agent actions via semantic similarity.

    Args:
        experiment_id: ID of experiment
        query: Natural language search query
        limit: Maximum results to return

    Returns:
        List of similar actions ranked by similarity score
    """
    if not _processor:
        raise HTTPException(status_code=503, detail="Semantic processor not initialized")
    
    try:
        results = await _processor.semantic_search(
            experiment_id=experiment_id,
            query=query,
            limit=limit
        )
        return {
            "experiment_id": experiment_id,
            "query": query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weekly-summaries")
async def get_weekly_summaries(
    experiment_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Fetch weekly summaries with pagination.

    Args:
        experiment_id: Filter by experiment ID (optional)
        limit: Number of summaries to return
        offset: Skip first N summaries

    Returns:
        List of weekly summary records
    """
    if not _summary_generator:
        raise HTTPException(status_code=503, detail="Summary generator not initialized")
    
    try:
        summaries, total = await _summary_generator.get_summaries(
            experiment_id=experiment_id,
            limit=limit,
            offset=offset,
        )
        return {
            "limit": limit,
            "offset": offset,
            "summaries": summaries,
            "total": total,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_id}/semantic-insights")
async def get_semantic_insights(experiment_id: str):
    """Get semantic insights for an experiment.

    Args:
        experiment_id: ID of experiment

    Returns:
        Semantic analysis including themes, anomalies, patterns
    """
    # TODO: Phase 6 - Implement clustering and analysis
    return {
        "experiment_id": experiment_id,
        "themes": [],
        "anomalies": [],
        "patterns": [],
    }

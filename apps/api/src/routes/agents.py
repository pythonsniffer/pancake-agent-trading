from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.database import get_db
from ..models.agent import AgentState, AgentStatus, AgentType

router = APIRouter()


class AgentResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    type: str
    status: str
    config: Optional[dict] = None
    success_count: int = 0
    error_count: int = 0
    total_actions: int = 0
    last_action: Optional[str] = None
    last_action_at: Optional[str] = None
    last_error: Optional[str] = None

    class Config:
        from_attributes = True


class AgentUpdateRequest(BaseModel):
    status: Optional[str] = None
    config: Optional[dict] = None


class AgentActionRequest(BaseModel):
    action: str
    parameters: Optional[dict] = Field(default_factory=dict)


# IMPORTANT: static routes MUST come before /{agent_id} to avoid path conflicts

@router.get("/stats/overview")
async def get_agents_stats(db: Session = Depends(get_db)):
    """Get overall agents statistics"""
    from sqlalchemy import func

    stats = db.query(
        func.count(AgentState.id).label('total'),
        func.sum(AgentState.success_count).label('total_successes'),
        func.sum(AgentState.error_count).label('total_errors'),
    ).first()

    status_counts = db.query(
        AgentState.status,
        func.count(AgentState.id).label('count')
    ).group_by(AgentState.status).all()

    type_counts = db.query(
        AgentState.type,
        func.count(AgentState.id).label('count')
    ).group_by(AgentState.type).all()

    return {
        "total_agents": stats.total,
        "total_successes": stats.total_successes or 0,
        "total_errors": stats.total_errors or 0,
        "by_status": {s.status.value if hasattr(s.status, 'value') else s.status: s.count for s in status_counts},
        "by_type": {t.type.value if hasattr(t.type, 'value') else t.type: t.count for t in type_counts},
    }


@router.get("")
async def get_agents(
    type: Optional[str] = Query(None, description="Filter by agent type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get all agents with optional filtering"""
    query = db.query(AgentState)

    if type:
        query = query.filter(AgentState.type == type)
    if status:
        query = query.filter(AgentState.status == status)

    agents = query.all()
    return {"data": [AgentResponse(**agent.to_dict()).model_dump() for agent in agents]}


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get a specific agent by ID"""
    agent = db.query(AgentState).filter(AgentState.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(**agent.to_dict())


@router.post("/{agent_id}/start")
async def start_agent(agent_id: str, db: Session = Depends(get_db)):
    """Start an agent"""
    agent = db.query(AgentState).filter(AgentState.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = AgentStatus.RUNNING
    agent.last_action = "Agent started"
    agent.last_action_at = datetime.utcnow()
    db.commit()

    return {"message": f"Agent {agent_id} started", "status": "RUNNING"}


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str, db: Session = Depends(get_db)):
    """Stop an agent"""
    agent = db.query(AgentState).filter(AgentState.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = AgentStatus.STOPPED
    agent.last_action = "Agent stopped"
    agent.last_action_at = datetime.utcnow()
    db.commit()

    return {"message": f"Agent {agent_id} stopped", "status": "STOPPED"}


@router.post("/{agent_id}/pause")
async def pause_agent(agent_id: str, db: Session = Depends(get_db)):
    """Pause an agent"""
    agent = db.query(AgentState).filter(AgentState.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = AgentStatus.PAUSED
    agent.last_action = "Agent paused"
    agent.last_action_at = datetime.utcnow()
    db.commit()

    return {"message": f"Agent {agent_id} paused", "status": "PAUSED"}


@router.get("/{agent_id}/actions")
async def get_agent_actions(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get recent actions for an agent"""
    agent = db.query(AgentState).filter(AgentState.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    actions = agent.short_term_memory or []

    return {
        "agent_id": agent_id,
        "actions": actions[:limit],
        "total": len(actions)
    }

"""
Vector Memory Store: Semantic storage and retrieval for agent learning.
Uses ChromaDB for vector storage and OpenAI embeddings for similarity search.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import hashlib

import chromadb
from chromadb.config import Settings as ChromaSettings
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry for the vector store"""
    id: str
    agent_name: str
    memory_type: str  # trade, market_condition, strategy_decision, error
    content: str
    metadata: Dict[str, Any]
    timestamp: int
    embedding: Optional[List[float]] = None
    importance_score: float = 1.0  # 0-1, higher = more important
    access_count: int = 0


@dataclass
class MemoryQuery:
    """Query for retrieving memories"""
    query_text: str
    agent_filter: Optional[str] = None
    memory_type_filter: Optional[str] = None
    top_k: int = 5
    time_range: Optional[tuple] = None  # (start_ts, end_ts)
    min_importance: float = 0.0


@dataclass
class SimilarScenario:
    """A similar historical scenario retrieved from memory"""
    memory: MemoryEntry
    similarity_score: float
    context_summary: str
    outcome: str
    lessons_learned: List[str]


class VectorMemoryStore:
    """
    Vector Memory Store for agent learning and decision support.

    Features:
    - Semantic storage of trading decisions, market conditions, outcomes
    - Similarity-based retrieval of historical scenarios
    - Importance scoring for memory prioritization
    - Temporal decay for outdated memories
    """

    def __init__(
        self,
        chroma_host: str = "localhost",
        chroma_port: int = 8000,
        embedding_function: Optional[Callable] = None,
        collection_name: str = "agent_memories"
    ):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.collection_name = collection_name
        self.embedding_function = embedding_function

        # Initialize ChromaDB client
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # Get or create collection
        self.collection = self._get_or_create_collection()

        # In-memory cache for frequent queries
        self.cache: Dict[str, List[MemoryEntry]] = {}
        self.cache_ttl = 300  # 5 minutes
        self.cache_timestamps: Dict[str, int] = {}

        logger.info(f"VectorMemoryStore initialized with collection: {collection_name}")

    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
            return collection
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Trading agent memories and decisions"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
            return collection

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using configured embedding function"""
        if self.embedding_function:
            return self.embedding_function(text)

        # Simple fallback: use hash-based pseudo-embedding
        # In production, use OpenAI, sentence-transformers, or similar
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        # Convert to float vector
        vec = [int(hash_val[i:i+8], 16) / 2**32 for i in range(0, 64, 8)]
        return vec

    def _generate_id(self, agent_name: str, timestamp: int, content_hash: str) -> str:
        """Generate unique ID for memory entry"""
        return f"{agent_name}_{timestamp}_{content_hash[:8]}"

    async def store(
        self,
        agent_name: str,
        memory_type: str,
        content: str,
        metadata: Dict[str, Any] = None,
        importance_score: float = 1.0
    ) -> str:
        """
        Store a new memory entry in the vector database.

        Args:
            agent_name: Name of the agent storing the memory
            memory_type: Type of memory (trade, market_condition, etc.)
            content: Textual content of the memory
            metadata: Additional structured data
            importance_score: Importance rating (0-1)

        Returns:
            Memory entry ID
        """
        try:
            timestamp = int(datetime.now().timestamp())
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            memory_id = self._generate_id(agent_name, timestamp, content_hash)

            # Generate embedding
            embedding = self._generate_embedding(content)

            # Create memory entry
            entry = MemoryEntry(
                id=memory_id,
                agent_name=agent_name,
                memory_type=memory_type,
                content=content,
                metadata=metadata or {},
                timestamp=timestamp,
                embedding=embedding,
                importance_score=importance_score
            )

            # Store in ChromaDB
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "agent_name": agent_name,
                    "memory_type": memory_type,
                    "timestamp": timestamp,
                    "importance_score": importance_score,
                    **{k: json.dumps(v) if isinstance(v, (dict, list)) else v
                       for k, v in (metadata or {}).items()}
                }]
            )

            logger.debug(f"Stored memory: {memory_id} for agent {agent_name}")
            return memory_id

        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise

    async def store_trade_memory(
        self,
        agent_name: str,
        trade_signal: Dict[str, Any],
        execution_result: Dict[str, Any],
        market_conditions: Dict[str, Any],
        strategy_used: str,
        outcome: str,
        profit_loss: float
    ) -> str:
        """
        Store a complete trade memory with rich context.

        This enables agents to learn from past trades by retrieving
        similar scenarios before making new decisions.
        """
        # Build rich content description
        content = f"""
        Trade executed on {market_conditions.get('chain', 'unknown')} chain.
        Strategy: {strategy_used}
        Tokens: {trade_signal.get('token_in', {}).get('symbol', '?')} -> {trade_signal.get('token_out', {}).get('symbol', '?')}
        Expected profit: ${trade_signal.get('expected_profit', 0):.2f}
        Actual profit: ${profit_loss:.2f}
        Outcome: {outcome}
        Market regime: {market_conditions.get('regime', 'unknown')}
        Volatility: {market_conditions.get('volatility', 0):.2f}%
        """

        # Calculate importance based on profit/loss magnitude
        importance = min(1.0, abs(profit_loss) / 100 + 0.3)
        if outcome == "FAILED":
            importance = max(importance, 0.8)  # Failed trades are important to remember

        metadata = {
            "trade_signal": trade_signal,
            "execution_result": execution_result,
            "market_conditions": market_conditions,
            "strategy_used": strategy_used,
            "outcome": outcome,
            "profit_loss": profit_loss,
            "token_pair": f"{trade_signal.get('token_in', {}).get('symbol', '?')}/{trade_signal.get('token_out', {}).get('symbol', '?')}",
            "chain": market_conditions.get('chain', 'unknown'),
        }

        return await self.store(
            agent_name=agent_name,
            memory_type="trade",
            content=content,
            metadata=metadata,
            importance_score=importance
        )

    async def query(self, query: MemoryQuery) -> List[SimilarScenario]:
        """
        Query the memory store for similar historical scenarios.

        This is the core RAG functionality that enables agents to
        learn from past experiences.
        """
        try:
            # Build where filter
            where_filter = {}
            if query.agent_filter:
                where_filter["agent_name"] = query.agent_filter
            if query.memory_type_filter:
                where_filter["memory_type"] = query.memory_type_filter
            if query.min_importance > 0:
                where_filter["importance_score"] = {"$gte": query.min_importance}

            # Add time range if specified
            if query.time_range:
                start_ts, end_ts = query.time_range
                where_filter["timestamp"] = {"$gte": start_ts, "$lte": end_ts}

            # Generate query embedding
            query_embedding = self._generate_embedding(query.query_text)

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=query.top_k,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )

            # Build SimilarScenario objects
            scenarios = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i, memory_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    document = results['documents'][0][i]
                    distance = results['distances'][0][i]

                    # Convert similarity (lower distance = higher similarity)
                    similarity = 1 - min(distance, 1.0)

                    # Reconstruct MemoryEntry
                    memory = MemoryEntry(
                        id=memory_id,
                        agent_name=metadata.get('agent_name', 'unknown'),
                        memory_type=metadata.get('memory_type', 'unknown'),
                        content=document,
                        metadata={k: json.loads(v) if isinstance(v, str) and v.startswith('{')
                                  else v for k, v in metadata.items()},
                        timestamp=metadata.get('timestamp', 0),
                        importance_score=metadata.get('importance_score', 1.0)
                    )

                    # Generate context summary and lessons
                    context_summary = self._generate_context_summary(memory)
                    lessons = self._extract_lessons(memory)

                    scenarios.append(SimilarScenario(
                        memory=memory,
                        similarity_score=similarity,
                        context_summary=context_summary,
                        outcome=metadata.get('outcome', 'unknown'),
                        lessons_learned=lessons
                    ))

            return sorted(scenarios, key=lambda x: x.similarity_score, reverse=True)

        except Exception as e:
            logger.error(f"Failed to query memories: {e}")
            return []

    def _generate_context_summary(self, memory: MemoryEntry) -> str:
        """Generate a human-readable summary of the memory context"""
        if memory.memory_type == "trade":
            token_pair = memory.metadata.get('token_pair', 'unknown')
            strategy = memory.metadata.get('strategy_used', 'unknown')
            pnl = memory.metadata.get('profit_loss', 0)
            return f"{strategy} trade on {token_pair} with PnL ${pnl:.2f}"
        elif memory.memory_type == "market_condition":
            regime = memory.metadata.get('regime', 'unknown')
            return f"Market in {regime} regime"
        else:
            return f"{memory.memory_type} event by {memory.agent_name}"

    def _extract_lessons(self, memory: MemoryEntry) -> List[str]:
        """Extract actionable lessons from a memory"""
        lessons = []

        if memory.memory_type == "trade":
            outcome = memory.metadata.get('outcome', 'unknown')
            pnl = memory.metadata.get('profit_loss', 0)
            expected = memory.metadata.get('trade_signal', {}).get('expected_profit', 0)

            if outcome == "FAILED":
                lessons.append("Transaction failed - check gas settings and network conditions")
            elif pnl < 0:
                lessons.append(f"Loss occurred: expected ${expected:.2f}, got ${pnl:.2f}")
                if memory.metadata.get('market_conditions', {}).get('regime') == 'VOLATILE':
                    lessons.append("Trade in volatile market had unexpected slippage")
            elif pnl > expected * 1.5:
                lessons.append("Trade outperformed expectations - favorable conditions")

        return lessons

    async def get_similar_trades(
        self,
        token_pair: str,
        strategy: str,
        market_regime: str,
        top_k: int = 5
    ) -> List[SimilarScenario]:
        """
        Get similar historical trades for decision support.

        Agents call this before executing to learn from past similar trades.
        """
        query_text = f"""
        Similar trades for {token_pair} using {strategy} strategy
        in {market_regime} market conditions
        """

        query = MemoryQuery(
            query_text=query_text,
            memory_type_filter="trade",
            top_k=top_k
        )

        return await self.query(query)

    async def get_agent_experiences(
        self,
        agent_name: str,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Get recent experiences for a specific agent"""
        query = MemoryQuery(
            query_text=f"Recent {memory_type or ''} experiences for {agent_name}",
            agent_filter=agent_name,
            memory_type_filter=memory_type,
            top_k=limit
        )

        scenarios = await self.query(query)
        return [s.memory for s in scenarios]

    async def get_performance_insights(
        self,
        strategy: Optional[str] = None,
        token_pair: Optional[str] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate performance insights from stored memories.

        Returns aggregate statistics and patterns for strategy improvement.
        """
        end_ts = int(datetime.now().timestamp())
        start_ts = end_ts - (time_range_days * 24 * 3600)

        query = MemoryQuery(
            query_text=f"Performance analysis for {strategy or 'all strategies'}",
            memory_type_filter="trade",
            time_range=(start_ts, end_ts),
            top_k=100
        )

        scenarios = await self.query(query)

        # Calculate statistics
        total_trades = len(scenarios)
        winning_trades = len([s for s in scenarios if s.outcome == "SUCCESS" and
                              s.memory.metadata.get('profit_loss', 0) > 0])
        losing_trades = len([s for s in scenarios if s.outcome == "SUCCESS" and
                             s.memory.metadata.get('profit_loss', 0) < 0])
        failed_trades = len([s for s in scenarios if s.outcome == "FAILED"])

        total_pnl = sum(s.memory.metadata.get('profit_loss', 0) for s in scenarios)

        # Group by strategy
        strategy_performance = {}
        for s in scenarios:
            strat = s.memory.metadata.get('strategy_used', 'unknown')
            if strat not in strategy_performance:
                strategy_performance[strat] = {"trades": 0, "pnl": 0, "wins": 0}
            strategy_performance[strat]["trades"] += 1
            strategy_performance[strat]["pnl"] += s.memory.metadata.get('profit_loss', 0)
            if s.memory.metadata.get('profit_loss', 0) > 0:
                strategy_performance[strat]["wins"] += 1

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "failed_trades": failed_trades,
            "win_rate": winning_trades / total_trades * 100 if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "avg_pnl_per_trade": total_pnl / total_trades if total_trades > 0 else 0,
            "strategy_performance": strategy_performance,
            "time_range_days": time_range_days,
        }

    async def cleanup_old_memories(self, days_to_keep: int = 90) -> int:
        """Remove memories older than specified days"""
        cutoff_ts = int(datetime.now().timestamp()) - (days_to_keep * 24 * 3600)

        try:
            # Query for old memories
            old_memories = self.collection.get(
                where={"timestamp": {"$lt": cutoff_ts}}
            )

            if old_memories['ids']:
                self.collection.delete(ids=old_memories['ids'])
                logger.info(f"Cleaned up {len(old_memories['ids'])} old memories")
                return len(old_memories['ids'])

            return 0
        except Exception as e:
            logger.error(f"Failed to cleanup old memories: {e}")
            return 0

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory store"""
        try:
            count = self.collection.count()
            return {
                "total_memories": count,
                "collection_name": self.collection_name,
                "chroma_host": self.chroma_host,
                "chroma_port": self.chroma_port,
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}


# Singleton instance
_memory_store: Optional[VectorMemoryStore] = None


async def get_memory_store(
    chroma_host: str = "localhost",
    chroma_port: int = 8000
) -> VectorMemoryStore:
    """Get or create the singleton memory store instance"""
    global _memory_store
    if _memory_store is None:
        _memory_store = VectorMemoryStore(
            chroma_host=chroma_host,
            chroma_port=chroma_port
        )
    return _memory_store

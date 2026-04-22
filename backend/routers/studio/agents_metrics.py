"""
StudioX — Agent Metrics Module
Tracks aggregate metrics per agent across all projects of a tenant:
  • activations (how many times the agent was invoked)
  • total_duration_seconds (sum of elapsed time when the agent was active)
  • last_used_at (ISO timestamp)
  • estimated_cost (USD) — computed from model + token usage when available

Storage: per-tenant at `settings.agent_metrics[agent_id] = {...}`

Design: ADDITIVE + FAIL-SILENT. All writes are wrapped in try/except so a
metrics failure never breaks a pipeline.
"""
from ._shared import *
from typing import Dict, Optional as Opt
from datetime import datetime, timezone

# Rough token→USD conversion for rough cost estimation.
# Prices approximate Anthropic Claude Sonnet 4.5 ($3 / 1M input, $15 / 1M output).
# For other models (GPT, Gemini) we use the same base — the purpose is an
# ORDER-OF-MAGNITUDE estimate, not invoice-grade accuracy.
_COST_PER_1M_INPUT_USD = 3.0
_COST_PER_1M_OUTPUT_USD = 15.0


def record_activation(
    tenant_id: str,
    agent_id: str,
    duration_seconds: float = 0.0,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    """
    Record a single agent activation + its associated cost and latency.
    Callers are expected to pass `duration_seconds` (wall-clock elapsed while
    the agent ran) and optionally `input_tokens` / `output_tokens` for cost.
    """
    try:
        settings = _get_settings(tenant_id)
        metrics = settings.get("agent_metrics") or {}
        entry = metrics.get(agent_id) or {
            "activations": 0,
            "total_duration_seconds": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "estimated_cost_usd": 0.0,
            "last_used_at": None,
        }

        entry["activations"] = int(entry.get("activations", 0)) + 1
        entry["total_duration_seconds"] = round(
            float(entry.get("total_duration_seconds", 0.0)) + float(duration_seconds), 2
        )
        entry["total_input_tokens"] = int(entry.get("total_input_tokens", 0)) + int(input_tokens)
        entry["total_output_tokens"] = int(entry.get("total_output_tokens", 0)) + int(output_tokens)

        delta_cost = (
            (input_tokens / 1_000_000.0) * _COST_PER_1M_INPUT_USD +
            (output_tokens / 1_000_000.0) * _COST_PER_1M_OUTPUT_USD
        )
        entry["estimated_cost_usd"] = round(
            float(entry.get("estimated_cost_usd", 0.0)) + float(delta_cost), 6
        )
        entry["last_used_at"] = datetime.now(timezone.utc).isoformat()

        metrics[agent_id] = entry
        settings["agent_metrics"] = metrics
        _save_settings(tenant_id, settings, flush_now=True)
    except Exception as e:
        logger.warning(f"record_activation({agent_id}) failed silently: {e}")


@router.get("/agents/metrics")
async def get_agent_metrics(tenant=Depends(get_current_tenant)):
    """
    Returns aggregate metrics for every agent that has been used at least once
    by this tenant.
    """
    settings = _get_settings(tenant["id"])
    metrics = settings.get("agent_metrics") or {}

    # Compute avg_latency_seconds on the fly (derived field, not stored)
    enriched: Dict[str, dict] = {}
    for agent_id, m in (metrics or {}).items():
        activations = int(m.get("activations", 0))
        total_dur = float(m.get("total_duration_seconds", 0.0))
        enriched[agent_id] = {
            **m,
            "avg_latency_seconds": round(total_dur / activations, 2) if activations > 0 else 0.0,
        }

    # Global totals
    totals = {
        "activations": sum(int(m.get("activations", 0)) for m in (metrics or {}).values()),
        "estimated_cost_usd": round(
            sum(float(m.get("estimated_cost_usd", 0.0)) for m in (metrics or {}).values()), 4
        ),
        "total_duration_seconds": round(
            sum(float(m.get("total_duration_seconds", 0.0)) for m in (metrics or {}).values()), 2
        ),
    }

    return {"metrics": enriched, "totals": totals}


@router.post("/agents/metrics/reset")
async def reset_agent_metrics(tenant=Depends(get_current_tenant)):
    """Zero-out all agent metrics for this tenant (admin button)."""
    settings = _get_settings(tenant["id"])
    settings["agent_metrics"] = {}
    _save_settings(tenant["id"], settings, flush_now=True)
    return {"status": "reset"}

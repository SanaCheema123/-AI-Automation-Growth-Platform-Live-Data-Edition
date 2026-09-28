from app.workflows.engine.registry import NODE_REGISTRY


def validate_definition(definition: dict) -> list[str]:
    errors = []
    steps = definition.get("steps")
    if not isinstance(steps, list) or not steps:
        return ["definition.steps must be a non-empty list"]
    if len(steps) > 100:
        errors.append("definition.steps may not exceed 100 nodes")
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"step {i} must be an object")
            continue
        node_type = step.get("type")
        config = step.get("config", {})
        if node_type not in NODE_REGISTRY:
            errors.append(f"step {i}: unsupported node type {node_type!r}")
        if not isinstance(config, dict):
            errors.append(f"step {i}: config must be an object")
            continue
        if node_type in {"ai_classify", "ai_generate"} and not str(config.get("prompt", "")).strip():
            errors.append(f"step {i}: {node_type} requires config.prompt")
        if node_type == "human_approval" and config.get("risk_level", "medium") not in {"low", "medium", "high"}:
            errors.append(f"step {i}: invalid approval risk_level")
        if node_type == "crm_update" and not isinstance(config.get("fields", {}), dict):
            errors.append(f"step {i}: crm_update fields must be an object")
    return errors

from app.workflows.nodes.trigger import TriggerNode
from app.workflows.nodes.ai_classify import AIClassifyNode
from app.workflows.nodes.ai_generate import AIGenerateNode
from app.workflows.nodes.approval import ApprovalNode
from app.workflows.nodes.crm_update import CRMUpdateNode

NODE_REGISTRY = {
    "trigger": TriggerNode,
    "ai_classify": AIClassifyNode,
    "ai_generate": AIGenerateNode,
    "human_approval": ApprovalNode,
    "crm_update": CRMUpdateNode,
}

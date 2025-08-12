"""
Campaign Brain Nodes

Individual processing nodes for the LangGraph campaign brain system.
Each node specializes in a specific aspect of campaign management.
"""

from .trait_detector import TraitDetectorNode
from .campaign_planner import CampaignPlannerNode
from .message_generator import MessageGeneratorNode
from .message_reviewer import MessageReviewerNode
from .quality_gatekeeper import QualityGatekeeperNode
from .injector import InjectorNode
from .memory_manager import MemoryManagerNode

__all__ = [
    'TraitDetectorNode',
    'CampaignPlannerNode', 
    'MessageGeneratorNode',
    'MessageReviewerNode',
    'QualityGatekeeperNode',
    'InjectorNode',
    'MemoryManagerNode'
]
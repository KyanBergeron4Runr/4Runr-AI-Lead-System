"""
Campaign Generator module for creating multi-step email campaigns
"""

try:
    from .generator import CampaignGenerator
    __all__ = ['CampaignGenerator']
except ImportError:
    # Fallback for testing without full dependencies
    __all__ = []
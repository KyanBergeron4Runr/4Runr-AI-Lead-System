"""
Google Enricher module for the 4Runr Autonomous Outreach System.

This module uses Google search to enrich leads with missing company information
and website URLs when we only have a person's name and LinkedIn profile.
"""

from .app import GoogleEnricherAgent

__all__ = ['GoogleEnricherAgent']
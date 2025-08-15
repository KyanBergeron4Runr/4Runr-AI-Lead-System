"""
LinkedIn Enricher module for the 4Runr Autonomous Outreach System.

This module extracts website URLs from LinkedIn company profiles
to populate the Website field for downstream processing.
"""

from .app import LinkedInEnricherAgent

__all__ = ['LinkedInEnricherAgent']
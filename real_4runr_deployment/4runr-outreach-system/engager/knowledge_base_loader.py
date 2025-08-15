"""
Knowledge Base Loader for the 4Runr Email Engager Upgrade.

Handles loading, caching, and validation of the 4Runr knowledge base content
with robust error handling and fallback mechanisms.
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional
from shared.logging_utils import get_logger


class KnowledgeBaseError(Exception):
    """Custom exception for knowledge base issues."""
    pass


class KnowledgeBaseLoader:
    """Manages loading and caching of 4Runr knowledge base content."""
    
    def __init__(self, knowledge_path: str = "data/4runr_knowledge.md"):
        """
        Initialize the Knowledge Base Loader.
        
        Args:
            knowledge_path: Path to the knowledge base file relative to project root
        """
        self.knowledge_path = knowledge_path
        self._cached_knowledge = None
        self._last_loaded = None
        self._cache_duration = 3600  # Cache for 1 hour
        self.logger = get_logger('engager')
        
        # Resolve absolute path
        project_root = Path(__file__).parent.parent
        self.absolute_path = project_root / knowledge_path
    
    def load_knowledge_base(self) -> str:
        """
        Load 4Runr knowledge base content with caching and error handling.
        
        Returns:
            Knowledge base content as string
            
        Raises:
            KnowledgeBaseError: If knowledge base cannot be loaded and no fallback available
        """
        # Check if cached version is still valid
        if self._is_cache_valid():
            self.logger.log_module_activity('engager', 'system', 'info', 
                                           {'message': 'Using cached knowledge base'})
            return self._cached_knowledge
        
        try:
            # Load from file
            knowledge_content = self._load_from_file()
            
            # Validate content
            if self._validate_knowledge_content(knowledge_content):
                self._cached_knowledge = knowledge_content
                self._last_loaded = time.time()
                
                self.logger.log_module_activity('engager', 'system', 'success', 
                                               {'message': f'Knowledge base loaded successfully from {self.knowledge_path}'})
                return knowledge_content
            else:
                raise KnowledgeBaseError("Knowledge base content validation failed")
                
        except FileNotFoundError:
            self.logger.log_module_activity('engager', 'system', 'warning', 
                                           {'message': f'Knowledge base file not found at {self.absolute_path}, using fallback'})
            return self._get_fallback_knowledge()
            
        except Exception as e:
            self.logger.log_error(e, {'action': 'load_knowledge_base', 'path': str(self.absolute_path)})
            return self._get_fallback_knowledge()
    
    def _load_from_file(self) -> str:
        """Load knowledge base content from file."""
        try:
            with open(self.absolute_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                raise KnowledgeBaseError("Knowledge base file is empty")
                
            return content
            
        except UnicodeDecodeError as e:
            raise KnowledgeBaseError(f"Knowledge base file encoding error: {e}")
    
    def _validate_knowledge_content(self, content: str) -> bool:
        """
        Validate knowledge base content structure and completeness.
        
        Args:
            content: Knowledge base content to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        if not content or len(content.strip()) < 100:
            return False
        
        # Check for key sections
        required_sections = [
            "4Runr Knowledge Base",
            "Core Philosophy",
            "Systems Thinking",
            "Infrastructure-First",
            "AI-as-a-Layer",
            "Business Value"
        ]
        
        content_lower = content.lower()
        missing_sections = []
        
        for section in required_sections:
            if section.lower() not in content_lower:
                missing_sections.append(section)
        
        if missing_sections:
            self.logger.log_module_activity('engager', 'system', 'warning', 
                                           {'message': f'Knowledge base missing sections: {missing_sections}'})
            return False
        
        return True
    
    def _get_fallback_knowledge(self) -> str:
        """
        Get fallback 4Runr knowledge base content when file is unavailable.
        
        Returns:
            Fallback knowledge base content
        """
        fallback_content = """# 4Runr Knowledge Base (Fallback)

## Core Philosophy

### Systems Thinking
4Runr approaches every challenge through a systems lens, understanding that true business transformation requires orchestrating multiple interconnected components. We don't solve isolated problems; we optimize entire ecosystems.

### Infrastructure-First Mindset
Before building features, we build foundations. Our infrastructure-first approach ensures that every solution is designed for scale, reliability, and long-term sustainability. We create the backbone that supports exponential growth.

### AI-as-a-Layer (Not a Tool)
AI isn't a feature we bolt on—it's a foundational layer that enhances every aspect of your operations. We integrate intelligence into your infrastructure, making your entire system smarter, more adaptive, and more capable.

### Business Value Language
Every technical decision maps directly to business outcomes. We speak in terms of competitive advantage, operational efficiency, risk mitigation, and revenue acceleration. Technology serves strategy, not the other way around.

## Strategic Messaging

**Bold and Direct**: We make clear, confident statements about what we can achieve.
**System-Level Thinking**: We talk about comprehensive solutions, not point fixes.
**Business-Focused**: Every conversation centers on business outcomes and strategic advantage.
**Evidence-Based**: We support our claims with concrete examples and proven methodologies.

## Key Value Propositions

- **Operational Excellence**: Eliminate friction between current operations and growth ambitions
- **Competitive Advantage**: Infrastructure advantage that lets you move faster than competition
- **Risk Mitigation**: Systems thinking that identifies and eliminates failure points
- **Future-Proofing**: Build foundation for tomorrow's opportunities, not just today's problems
"""
        
        # Cache the fallback content
        self._cached_knowledge = fallback_content
        self._last_loaded = time.time()
        
        self.logger.log_module_activity('engager', 'system', 'info', 
                                       {'message': 'Using fallback 4Runr knowledge base'})
        
        return fallback_content
    
    def _is_cache_valid(self) -> bool:
        """Check if cached knowledge base is still valid."""
        if not self._cached_knowledge or not self._last_loaded:
            return False
        
        return (time.time() - self._last_loaded) < self._cache_duration
    
    def get_knowledge_summary(self) -> Dict[str, str]:
        """
        Extract key knowledge components for message generation.
        
        Returns:
            Dictionary with key knowledge components
        """
        knowledge = self.load_knowledge_base()
        
        # Extract key sections for easy access
        summary = {
            'systems_thinking': 'We approach every challenge through a systems lens, optimizing entire ecosystems rather than solving isolated problems.',
            'infrastructure_first': 'We build foundations before features, ensuring every solution is designed for scale, reliability, and long-term sustainability.',
            'ai_as_layer': 'AI is a foundational layer that enhances every aspect of operations, making entire systems smarter and more adaptive.',
            'business_value': 'Every technical decision maps to business outcomes: competitive advantage, operational efficiency, and revenue acceleration.',
            'tone': 'Bold, direct, system-level thinking focused on business outcomes and strategic advantage.',
            'value_props': 'Operational excellence, competitive advantage, risk mitigation, and future-proofing through intelligent infrastructure.'
        }
        
        return summary
    
    def validate_knowledge_base(self) -> bool:
        """
        Validate knowledge base availability and content quality.
        
        Returns:
            True if knowledge base is valid and accessible, False otherwise
        """
        try:
            content = self.load_knowledge_base()
            return self._validate_knowledge_content(content)
        except Exception as e:
            self.logger.log_error(e, {'action': 'validate_knowledge_base'})
            return False
    
    def refresh_cache(self) -> bool:
        """
        Force refresh of cached knowledge base content.
        
        Returns:
            True if refresh successful, False otherwise
        """
        try:
            self._cached_knowledge = None
            self._last_loaded = None
            self.load_knowledge_base()
            return True
        except Exception as e:
            self.logger.log_error(e, {'action': 'refresh_cache'})
            return False


def load_knowledge_base(path: str = "data/4runr_knowledge.md") -> str:
    """
    Convenience function to load knowledge base content.
    
    Args:
        path: Path to knowledge base file
        
    Returns:
        Knowledge base content as string
    """
    loader = KnowledgeBaseLoader(path)
    return loader.load_knowledge_base()
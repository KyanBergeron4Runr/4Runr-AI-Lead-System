"""
Memory Manager Node

Tracks lead interactions and campaign history for informed decision-making.
Provides memory-aware context to other nodes and learns from campaign outcomes.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .base_node import CampaignNode
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from campaign_state import CampaignState


class MemoryManagerNode(CampaignNode):
    """Manages lead memory and campaign history"""
    
    def __init__(self, config):
        super().__init__(config)
        self.memory_storage = {}  # In-memory storage for Phase 1
        self.memory_retention_days = 90
    
    async def _execute_node_logic(self, state: CampaignState) -> CampaignState:
        """Execute memory management logic"""
        
        lead_id = self._get_lead_identifier(state.lead_data)
        
        # Retrieve existing memory
        existing_memory = self._get_lead_memory(lead_id)
        
        # Update memory with current execution
        updated_memory = self._update_lead_memory(existing_memory, state)
        
        # Store updated memory
        self._store_lead_memory(lead_id, updated_memory)
        
        # Generate insights from memory
        insights = self._generate_memory_insights(updated_memory, state)
        
        # Update state with memory context
        state.memory_context = {
            'lead_id': lead_id,
            'previous_attempts': updated_memory.get('campaign_attempts', []),
            'trait_history': updated_memory.get('traits_history', []),
            'quality_history': updated_memory.get('quality_scores_history', []),
            'best_performing_angles': updated_memory.get('best_performing_angles', []),
            'failed_approaches': updated_memory.get('failed_approaches', []),
            'last_contact_date': updated_memory.get('last_contact_date'),
            'total_attempts': updated_memory.get('total_attempts', 0),
            'success_rate': updated_memory.get('success_rate', 0.0)
        }
        
        state.historical_insights = insights
        
        # Log memory insights
        self.log_decision(
            state,
            f"Retrieved memory for lead {lead_id}",
            f"Previous attempts: {updated_memory.get('total_attempts', 0)}, Success rate: {updated_memory.get('success_rate', 0):.1f}%"
        )
        
        self.logger.info(f"Memory context loaded: {len(insights)} insights, {updated_memory.get('total_attempts', 0)} previous attempts")
        
        return state
    
    def _get_lead_identifier(self, lead_data: Dict[str, Any]) -> str:
        """Generate consistent lead identifier"""
        
        # Use lead ID if available
        if lead_data.get('id'):
            return str(lead_data['id'])
        
        # Generate hash from email + company
        email = lead_data.get('Email', '').lower().strip()
        company = lead_data.get('Company', '').lower().strip()
        
        if email:
            identifier_string = f"{email}_{company}"
            return hashlib.md5(identifier_string.encode()).hexdigest()[:12]
        
        # Fallback to name + company hash
        name = lead_data.get('Name', '').lower().strip()
        identifier_string = f"{name}_{company}"
        return hashlib.md5(identifier_string.encode()).hexdigest()[:12]
    
    def _get_lead_memory(self, lead_id: str) -> Dict[str, Any]:
        """Retrieve existing memory for a lead"""
        
        memory = self.memory_storage.get(lead_id, {})
        
        # Clean up old memory entries
        if memory:
            memory = self._cleanup_old_memory(memory)
        
        return memory
    
    def _update_lead_memory(self, existing_memory: Dict[str, Any], state: CampaignState) -> Dict[str, Any]:
        """Update lead memory with current execution"""
        
        # Initialize memory structure if new
        if not existing_memory:
            existing_memory = {
                'lead_id': self._get_lead_identifier(state.lead_data),
                'first_contact_date': datetime.now().isoformat(),
                'traits_history': [],
                'campaign_attempts': [],
                'quality_scores_history': [],
                'response_history': [],
                'best_performing_angles': [],
                'failed_approaches': [],
                'total_attempts': 0,
                'successful_attempts': 0,
                'success_rate': 0.0
            }
        
        # Update basic info
        existing_memory['last_contact_date'] = datetime.now().isoformat()
        existing_memory['total_attempts'] = existing_memory.get('total_attempts', 0) + 1
        
        # Add current traits to history
        if state.traits:
            trait_entry = {
                'traits': state.traits,
                'confidence': state.trait_confidence,
                'primary_trait': state.primary_trait,
                'timestamp': datetime.now().isoformat()
            }
            existing_memory['traits_history'].append(trait_entry)
            
            # Keep only last 5 trait entries
            existing_memory['traits_history'] = existing_memory['traits_history'][-5:]
        
        # Add current campaign attempt
        campaign_attempt = {
            'execution_id': state.execution_id,
            'messaging_angle': state.messaging_angle,
            'campaign_tone': state.campaign_tone,
            'campaign_sequence': state.campaign_sequence,
            'overall_quality_score': state.overall_quality_score,
            'final_status': state.final_status.value,
            'retry_count': state.retry_count,
            'timestamp': datetime.now().isoformat()
        }
        existing_memory['campaign_attempts'].append(campaign_attempt)
        
        # Keep only last 10 attempts
        existing_memory['campaign_attempts'] = existing_memory['campaign_attempts'][-10:]
        
        # Add quality score to history
        if state.overall_quality_score > 0:
            existing_memory['quality_scores_history'].append({
                'score': state.overall_quality_score,
                'messaging_angle': state.messaging_angle,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 scores
            existing_memory['quality_scores_history'] = existing_memory['quality_scores_history'][-10:]
        
        # Update performance tracking
        self._update_performance_tracking(existing_memory, state)
        
        return existing_memory
    
    def _update_performance_tracking(self, memory: Dict[str, Any], state: CampaignState):
        """Update performance tracking in memory"""
        
        from campaign_brain import CampaignStatus
        
        # Track successful approaches
        if state.final_status == CampaignStatus.APPROVED:
            memory['successful_attempts'] = memory.get('successful_attempts', 0) + 1
            
            # Track best performing angles
            angle = state.messaging_angle
            if angle not in memory['best_performing_angles']:
                memory['best_performing_angles'].append(angle)
            
            # Remove from failed approaches if it was there
            if angle in memory.get('failed_approaches', []):
                memory['failed_approaches'].remove(angle)
        
        # Track failed approaches
        elif state.final_status in [CampaignStatus.MANUAL_REVIEW, CampaignStatus.STALLED]:
            angle = state.messaging_angle
            if angle not in memory.get('failed_approaches', []):
                memory['failed_approaches'].append(angle)
            
            # Keep only last 5 failed approaches
            memory['failed_approaches'] = memory['failed_approaches'][-5:]
        
        # Calculate success rate
        total = memory.get('total_attempts', 1)
        successful = memory.get('successful_attempts', 0)
        memory['success_rate'] = (successful / total) * 100 if total > 0 else 0.0
    
    def _store_lead_memory(self, lead_id: str, memory: Dict[str, Any]):
        """Store updated memory"""
        
        self.memory_storage[lead_id] = memory
        
        # In production, this would save to Redis or database
        self.logger.debug(f"Memory updated for lead {lead_id}: {memory.get('total_attempts', 0)} attempts")
    
    def _generate_memory_insights(self, memory: Dict[str, Any], state: CampaignState) -> List[str]:
        """Generate actionable insights from memory"""
        
        insights = []
        
        # Previous attempt insights
        total_attempts = memory.get('total_attempts', 0)
        if total_attempts > 1:
            insights.append(f"This is attempt #{total_attempts} for this lead")
            
            success_rate = memory.get('success_rate', 0)
            if success_rate > 0:
                insights.append(f"Historical success rate: {success_rate:.1f}%")
            else:
                insights.append("No previous successful campaigns for this lead")
        
        # Trait consistency insights
        trait_history = memory.get('traits_history', [])
        if len(trait_history) > 1:
            current_traits = set(state.traits)
            previous_traits = set(trait_history[-2]['traits'])
            
            if current_traits == previous_traits:
                insights.append("Trait detection is consistent with previous analysis")
            else:
                new_traits = current_traits - previous_traits
                if new_traits:
                    insights.append(f"New traits detected: {', '.join(new_traits)}")
        
        # Quality score trends
        quality_history = memory.get('quality_scores_history', [])
        if len(quality_history) > 1:
            recent_scores = [entry['score'] for entry in quality_history[-3:]]
            avg_score = sum(recent_scores) / len(recent_scores)
            
            if state.overall_quality_score > avg_score + 10:
                insights.append("Quality score significantly improved from previous attempts")
            elif state.overall_quality_score < avg_score - 10:
                insights.append("Quality score declined from previous attempts")
        
        # Best performing angle insights
        best_angles = memory.get('best_performing_angles', [])
        if best_angles and state.messaging_angle in best_angles:
            insights.append(f"Using previously successful messaging angle: {state.messaging_angle}")
        
        # Failed approach warnings
        failed_approaches = memory.get('failed_approaches', [])
        if failed_approaches and state.messaging_angle in failed_approaches:
            insights.append(f"Warning: {state.messaging_angle} has failed previously for this lead")
        
        # Timing insights
        last_contact = memory.get('last_contact_date')
        if last_contact:
            try:
                last_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                days_since = (datetime.now() - last_date).days
                
                if days_since < 30:
                    insights.append(f"Recent contact: {days_since} days ago")
                elif days_since > 180:
                    insights.append(f"Long gap since last contact: {days_since} days ago")
            except:
                pass
        
        return insights
    
    def _cleanup_old_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old memory entries"""
        
        cutoff_date = datetime.now() - timedelta(days=self.memory_retention_days)
        
        # Clean up old campaign attempts
        if 'campaign_attempts' in memory:
            memory['campaign_attempts'] = [
                attempt for attempt in memory['campaign_attempts']
                if self._is_recent_entry(attempt.get('timestamp'), cutoff_date)
            ]
        
        # Clean up old trait history
        if 'traits_history' in memory:
            memory['traits_history'] = [
                entry for entry in memory['traits_history']
                if self._is_recent_entry(entry.get('timestamp'), cutoff_date)
            ]
        
        # Clean up old quality scores
        if 'quality_scores_history' in memory:
            memory['quality_scores_history'] = [
                entry for entry in memory['quality_scores_history']
                if self._is_recent_entry(entry.get('timestamp'), cutoff_date)
            ]
        
        return memory
    
    def _is_recent_entry(self, timestamp_str: str, cutoff_date: datetime) -> bool:
        """Check if entry is recent enough to keep"""
        
        if not timestamp_str:
            return False
        
        try:
            entry_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return entry_date > cutoff_date
        except:
            return False
    
    def validate_input(self, state: CampaignState) -> bool:
        """Validate input for memory management"""
        if not super().validate_input(state):
            return False
        
        # Memory management can work with minimal data
        return True
    
    def get_memory_summary(self, lead_id: str) -> Dict[str, Any]:
        """Get memory summary for a specific lead"""
        
        memory = self._get_lead_memory(lead_id)
        
        if not memory:
            return {'lead_id': lead_id, 'no_memory': True}
        
        return {
            'lead_id': lead_id,
            'total_attempts': memory.get('total_attempts', 0),
            'success_rate': memory.get('success_rate', 0.0),
            'last_contact_date': memory.get('last_contact_date'),
            'best_performing_angles': memory.get('best_performing_angles', []),
            'failed_approaches': memory.get('failed_approaches', []),
            'recent_quality_scores': [
                entry['score'] for entry in memory.get('quality_scores_history', [])[-3:]
            ],
            'consistent_traits': self._get_consistent_traits(memory)
        }
    
    def _get_consistent_traits(self, memory: Dict[str, Any]) -> List[str]:
        """Get traits that appear consistently across attempts"""
        
        trait_history = memory.get('traits_history', [])
        if len(trait_history) < 2:
            return []
        
        # Count trait frequency
        trait_counts = {}
        for entry in trait_history:
            for trait in entry.get('traits', []):
                trait_counts[trait] = trait_counts.get(trait, 0) + 1
        
        # Return traits that appear in most attempts
        threshold = len(trait_history) * 0.6  # 60% of attempts
        consistent_traits = [
            trait for trait, count in trait_counts.items()
            if count >= threshold
        ]
        
        return consistent_traits
"""
Message Generator Node

Uses GPT-4o with specialized prompts to create personalized campaign messages.
Loads prompts from external .j2 templates and generates subject + body content.
"""

import os
import openai
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from typing import Dict, Any, List
from .base_node import CampaignNode, RetryableError, FatalError
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from campaign_state import CampaignState, CampaignMessage


class MessageGeneratorNode(CampaignNode):
    """Generates campaign messages using GPT-4o and modular prompts"""
    
    def __init__(self, config):
        super().__init__(config)
        self._initialize_openai()
        self._initialize_templates()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        if not self.config.openai_api_key:
            raise FatalError("OpenAI API key not configured")
        
        self.openai_client = openai.OpenAI(api_key=self.config.openai_api_key)
        
        # Test API connection
        try:
            # Make a minimal test call
            self.openai_client.models.list()
            self.logger.info("OpenAI API connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect to OpenAI API: {str(e)}")
            raise FatalError(f"OpenAI API connection failed: {str(e)}")
    
    def _initialize_templates(self):
        """Initialize Jinja2 template environment"""
        template_dir = Path(__file__).parent.parent / "prompts"
        template_dir.mkdir(exist_ok=True)
        
        self.template_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Create default templates if they don't exist
        self._create_default_templates(template_dir)
    
    def _create_default_templates(self, template_dir: Path):
        """Create default prompt templates if they don't exist"""
        
        templates = {
            'hook.j2': '''You are a strategic outreach specialist for 4Runr, creating the first message in a campaign sequence.

LEAD CONTEXT:
- Name: {{ lead_data.Name }}
- Role: {{ lead_data.Title }}
- Company: {{ lead_data.Company }}

COMPANY INSIGHTS:
- Description: {{ company_data.description }}
- Services: {{ company_data.services }}
- Tone: {{ company_data.tone }}

STRATEGIC CONTEXT:
- Detected Traits: {{ traits | join(', ') }}
- Messaging Angle: {{ messaging_angle }}
- Campaign Tone: {{ campaign_tone }}
- Primary Trait: {{ primary_trait }}

REQUIREMENTS:
Create a hook message that grabs attention with strategic insight and positions 4Runr as a valuable strategic partner.

{% if messaging_angle == 'competitive_advantage' %}
- Focus on market differentiation and competitive positioning
- Highlight how market dynamics are shifting
- Position 4Runr as enabling competitive advantage
{% elif messaging_angle == 'technical_innovation' %}
- Focus on technical excellence and innovation
- Discuss technology trends and architectural challenges
- Position 4Runr as technical innovation partner
{% elif messaging_angle == 'growth_acceleration' %}
- Focus on scaling and growth opportunities
- Discuss growth challenges and market expansion
- Position 4Runr as growth acceleration partner
{% else %}
- Focus on operational efficiency and business optimization
- Discuss industry trends and operational challenges
- Position 4Runr as strategic optimization partner
{% endif %}

TONE GUIDELINES:
{% if campaign_tone == 'executive' %}
- Use strategic, high-level business language
- Focus on competitive insights and market positioning
- Be authoritative but not pushy
{% elif campaign_tone == 'technical' %}
- Use precise, technical language
- Focus on architecture and technical excellence
- Be detailed but accessible
{% else %}
- Use professional, clear business language
- Focus on business value and outcomes
- Be approachable but strategic
{% endif %}

STRUCTURE:
1. Personalized greeting using lead name
2. Strategic insight or market observation relevant to their company/industry
3. Light connection to 4Runr's capabilities (subtle, not salesy)
4. Soft call-to-action (question or suggestion for brief conversation)
5. Professional signature

Keep under 150 words. Make it feel researched and strategic, not templated.

Generate both SUBJECT LINE and MESSAGE BODY.''',

            'proof.j2': '''You are a strategic outreach specialist for 4Runr, creating the second message in a campaign sequence that demonstrates differentiation and value.

LEAD CONTEXT:
- Name: {{ lead_data.Name }}
- Role: {{ lead_data.Title }}
- Company: {{ lead_data.Company }}

COMPANY INSIGHTS:
- Description: {{ company_data.description }}
- Services: {{ company_data.services }}
- Tone: {{ company_data.tone }}

STRATEGIC CONTEXT:
- Detected Traits: {{ traits | join(', ') }}
- Messaging Angle: {{ messaging_angle }}
- Campaign Tone: {{ campaign_tone }}
- Primary Trait: {{ primary_trait }}

REQUIREMENTS:
Create a proof message that shows differentiation through evidence and proof points without sounding like a pitch.

{% if messaging_angle == 'competitive_advantage' %}
- Share market observations about what separates winners from followers
- Provide proof points about competitive differentiation
- Show how 4Runr enables strategic advantage
{% elif messaging_angle == 'technical_innovation' %}
- Share insights about technical architecture and innovation
- Provide proof points about technical excellence
- Show how 4Runr drives technical innovation
{% elif messaging_angle == 'growth_acceleration' %}
- Share observations about scaling challenges and solutions
- Provide proof points about growth acceleration
- Show how 4Runr enables rapid scaling
{% else %}
- Share insights about operational excellence and optimization
- Provide proof points about efficiency improvements
- Show how 4Runr drives operational excellence
{% endif %}

TONE GUIDELINES:
{% if campaign_tone == 'executive' %}
- Use strategic, results-oriented language
- Focus on business outcomes and competitive positioning
- Be confident but consultative
{% elif campaign_tone == 'technical' %}
- Use technical depth with architectural focus
- Focus on technical solutions and innovation
- Be precise but solution-oriented
{% else %}
- Use professional, value-focused language
- Focus on business benefits and outcomes
- Be credible but approachable
{% endif %}

STRUCTURE:
1. Reference to previous outreach (subtle)
2. Market observation or insight ("From what we've seen...")
3. Differentiation proof points (2-3 specific examples)
4. Subtle connection to their situation
5. Soft value demonstration
6. Professional signature

Keep under 175 words. Focus on proof and differentiation, not selling.

Generate both SUBJECT LINE and MESSAGE BODY.''',

            'fomo.j2': '''You are a strategic outreach specialist for 4Runr, creating the final message in a campaign sequence that creates urgency about competitive advantage and timing.

LEAD CONTEXT:
- Name: {{ lead_data.Name }}
- Role: {{ lead_data.Title }}
- Company: {{ lead_data.Company }}

COMPANY INSIGHTS:
- Description: {{ company_data.description }}
- Services: {{ company_data.services }}
- Tone: {{ company_data.tone }}

STRATEGIC CONTEXT:
- Detected Traits: {{ traits | join(', ') }}
- Messaging Angle: {{ messaging_angle }}
- Campaign Tone: {{ campaign_tone }}
- Primary Trait: {{ primary_trait }}

REQUIREMENTS:
Create a FOMO message that creates urgency about competitive advantage and market timing while maintaining professionalism.

{% if messaging_angle == 'competitive_advantage' %}
- Reference competitive activity and market movement
- Create urgency about maintaining competitive edge
- Position timing as critical for strategic advantage
{% elif messaging_angle == 'technical_innovation' %}
- Reference technology trends and innovation cycles
- Create urgency about technical leadership
- Position timing as critical for innovation advantage
{% elif messaging_angle == 'growth_acceleration' %}
- Reference market opportunities and growth windows
- Create urgency about scaling timing
- Position timing as critical for growth advantage
{% else %}
- Reference industry trends and optimization opportunities
- Create urgency about operational excellence
- Position timing as critical for efficiency advantage
{% endif %}

TONE GUIDELINES:
{% if campaign_tone == 'executive' %}
- Use urgent but strategic language
- Focus on competitive timing and market dynamics
- Be direct but respectful
{% elif campaign_tone == 'technical' %}
- Use technical urgency with innovation focus
- Focus on technology cycles and technical timing
- Be precise but compelling
{% else %}
- Use professional urgency with business focus
- Focus on market timing and business opportunities
- Be compelling but professional
{% endif %}

STRUCTURE:
1. Brief reference to previous outreach
2. Competitive landscape observation
3. Urgency about timing and market dynamics
4. Final opportunity positioning
5. Clear but respectful call-to-action
6. Professional signature with finality

Keep under 125 words. This is the final outreach - make it count but stay professional.

Generate both SUBJECT LINE and MESSAGE BODY.'''
        }
        
        for filename, content in templates.items():
            template_file = template_dir / filename
            if not template_file.exists():
                template_file.write_text(content)
                self.logger.info(f"Created default template: {filename}")
    
    async def _execute_node_logic(self, state: CampaignState) -> CampaignState:
        """Execute message generation logic"""
        
        generated_messages = []
        
        # Check if we should use fallback mode
        if state.fallback_mode:
            self.logger.info(f"Using fallback mode due to: {state.data_quality.get('fallback_reason', 'insufficient_data')}")
            return await self._generate_fallback_messages(state)
        
        # Generate messages for each type in the campaign sequence
        for message_type in state.campaign_sequence:
            try:
                # Track generation attempt
                attempt_key = f"{message_type}_attempt"
                current_attempt = state.generation_attempts.get(attempt_key, 0) + 1
                state.generation_attempts[attempt_key] = current_attempt
                
                self.logger.info(f"Generating {message_type} message (attempt {current_attempt})")
                
                # Generate message
                message = await self._generate_single_message(
                    message_type, state, current_attempt
                )
                
                generated_messages.append(message)
                
            except Exception as e:
                error_msg = f"Failed to generate {message_type} message: {str(e)}"
                state.generation_errors.append(error_msg)
                self.logger.error(error_msg)
                
                # Create placeholder message for failed generation
                placeholder_message = CampaignMessage(
                    message_type=message_type,
                    subject=f"[GENERATION FAILED] {message_type}",
                    body=f"Message generation failed: {str(e)}",
                    generation_attempt=current_attempt,
                    quality_score=0.0
                )
                generated_messages.append(placeholder_message)
        
        # Update state with generated messages
        state.messages = generated_messages
        
        # Log generation results
        successful_messages = len([m for m in generated_messages if m.quality_score > 0])
        self.log_decision(
            state,
            f"Generated {successful_messages}/{len(generated_messages)} messages successfully",
            f"Types: {[m.message_type for m in generated_messages]}"
        )
        
        return state
    
    async def _generate_single_message(self, message_type: str, state: CampaignState, 
                                     attempt: int) -> CampaignMessage:
        """Generate a single message using GPT-4o"""
        
        # Load and render prompt template
        prompt = self._render_prompt_template(message_type, state)
        
        # Add retry context if this is a retry attempt
        if attempt > 1:
            prompt += f"\n\nNOTE: This is attempt #{attempt}. Previous attempts had quality issues. Please ensure this message is highly personalized, strategic, and follows 4Runr's elevated positioning."
        
        try:
            # Call GPT-4o
            response = await self._call_openai(prompt)
            
            # Parse response into subject and body
            subject, body = self._parse_gpt_response(response)
            
            # Create message object
            message = CampaignMessage(
                message_type=message_type,
                subject=subject,
                body=body,
                generation_attempt=attempt,
                word_count=len(body.split()),
                quality_score=50.0  # Initial score, will be updated by reviewer
            )
            
            self.logger.debug(f"Generated {message_type} message: {len(body)} chars, {message.word_count} words")
            
            return message
            
        except Exception as e:
            self.logger.error(f"GPT-4o generation failed for {message_type}: {str(e)}")
            raise RetryableError(f"Message generation failed: {str(e)}")
    
    def _render_prompt_template(self, message_type: str, state: CampaignState) -> str:
        """Render prompt template with state data"""
        
        template_name = f"{message_type}.j2"
        
        try:
            template = self.template_env.get_template(template_name)
        except TemplateNotFound:
            # Fallback to generic template
            self.logger.warning(f"Template {template_name} not found, using hook.j2 as fallback")
            template = self.template_env.get_template("hook.j2")
        
        # Prepare template variables
        template_vars = {
            'lead_data': state.lead_data,
            'company_data': state.company_data,
            'scraped_content': state.scraped_content,
            'traits': state.traits,
            'messaging_angle': state.messaging_angle,
            'campaign_tone': state.campaign_tone,
            'primary_trait': state.primary_trait,
            'message_type': message_type
        }
        
        return template.render(**template_vars)
    
    async def _call_openai(self, prompt: str) -> str:
        """Make API call to GPT-4o"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strategic outreach specialist for 4Runr, a company that helps businesses optimize operations through AI and strategic consulting. Your role is to write personalized, helpful outreach messages that show genuine understanding of the recipient's business and offer strategic value. Always maintain 4Runr's elevated positioning: bold, strategic, and consultative - never pushy or salesy."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.config.openai_max_tokens,
                temperature=self.config.openai_temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenAI API call failed: {str(e)}")
            raise RetryableError(f"OpenAI API error: {str(e)}")
    
    def _parse_gpt_response(self, response: str) -> tuple[str, str]:
        """Parse GPT response into subject and body"""
        
        lines = response.strip().split('\n')
        subject = ""
        body = ""
        
        # Look for subject line indicators
        subject_indicators = ['subject:', 'subject line:', 'subject -', '**subject']
        body_indicators = ['body:', 'message:', 'message body:', '**message', '**body']
        
        current_section = None
        body_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check for subject line
            for indicator in subject_indicators:
                if line_lower.startswith(indicator):
                    subject = line[len(indicator):].strip().strip('*').strip()
                    current_section = 'subject'
                    break
            
            # Check for body
            for indicator in body_indicators:
                if line_lower.startswith(indicator):
                    current_section = 'body'
                    body_start = line[len(indicator):].strip()
                    if body_start:
                        body_lines.append(body_start)
                    break
            else:
                # If we're in body section, add the line
                if current_section == 'body' and line.strip():
                    body_lines.append(line.strip())
        
        # If no clear structure found, try to extract from response
        if not subject and not body_lines:
            # Look for first line as potential subject
            if lines:
                potential_subject = lines[0].strip()
                if len(potential_subject) < 100:  # Reasonable subject length
                    subject = potential_subject
                    body_lines = lines[1:]
                else:
                    # Treat entire response as body
                    body_lines = lines
        
        body = '\n'.join(body_lines).strip()
        
        # Fallback if parsing failed
        if not subject:
            subject = "Strategic Partnership Opportunity"
        if not body:
            body = response.strip()
        
        return subject, body
    
    def validate_input(self, state: CampaignState) -> bool:
        """Validate input for message generation"""
        if not super().validate_input(state):
            return False
        
        # Check if we have campaign sequence
        if not state.campaign_sequence:
            self.logger.error("No campaign sequence defined")
            return False
        
        # Check if we have messaging angle
        if not state.messaging_angle:
            self.logger.error("No messaging angle defined")
            return False
        
        return True
    
    async def _generate_fallback_messages(self, state: CampaignState) -> CampaignState:
        """Generate bold, curiosity-driven messages when data quality is low"""
        
        generated_messages = []
        fallback_reason = state.data_quality.get('fallback_reason', 'insufficient_data')
        
        # Select fallback prompt based on reason
        fallback_prompts = self._get_fallback_prompts()
        selected_prompt = fallback_prompts.get(fallback_reason, fallback_prompts['default'])
        
        # Generate a single powerful message instead of sequence
        try:
            self.logger.info(f"Generating fallback message using {fallback_reason} prompt")
            
            message = await self._generate_fallback_message(state, selected_prompt)
            generated_messages.append(message)
            
            # Update state
            state.messages = generated_messages
            
            self.log_decision(
                state,
                f"Generated fallback message",
                f"Used {fallback_reason} prompt due to low data quality"
            )
            
        except Exception as e:
            error_msg = f"Failed to generate fallback message: {str(e)}"
            state.generation_errors.append(error_msg)
            self.logger.error(error_msg)
            
            # Create emergency fallback
            emergency_message = self._create_emergency_fallback(state)
            generated_messages.append(emergency_message)
            state.messages = generated_messages
        
        return state
    
    def _get_fallback_prompts(self) -> Dict[str, str]:
        """Get fallback prompt templates for different scenarios"""
        
        return {
            'no_website_data': '''You are creating a bold, curiosity-driven outreach message for 4Runr when we have minimal company data.

LEAD INFO:
- Name: {{ lead_data.Name }}
- Role: {{ lead_data.Title }}
- Company: {{ lead_data.Company }}

STRATEGY: Create intrigue and curiosity without relying on company-specific insights.

PROMPT TEMPLATE:
Hi {{first_name}},

I know this might feel out of the blue — but we've been quietly helping mid-sized teams unlock serious performance gains in the background (often without anyone noticing).

If you're even slightly curious about what that looks like, happy to share.

– 4Runr Team

REQUIREMENTS:
- Use bold, confident language
- Create curiosity without being pushy
- Keep under 50 words
- No filler or generic business speak
- Strong, intriguing opening
- Soft but confident CTA

Generate SUBJECT LINE and MESSAGE BODY.''',

            'low_signal_website': '''You are creating a bold outreach message for 4Runr when the company website has generic/vague content.

LEAD INFO:
- Name: {{ lead_data.Name }}
- Role: {{ lead_data.Title }}
- Company: {{ lead_data.Company }}

STRATEGY: Acknowledge the challenge of standing out and create curiosity about our different approach.

PROMPT TEMPLATE:
Hi {{first_name}},

Most outreach you get probably sounds the same (we know because we used to do it too).

We've found a different way to help companies like {{company}} — one that actually moves the needle instead of just adding to the noise.

Worth a 5-minute conversation?

– 4Runr Team

REQUIREMENTS:
- Acknowledge the noise problem
- Position 4Runr as different/better
- Create curiosity about our approach
- Keep under 60 words
- Confident but not arrogant
- Clear, simple CTA

Generate SUBJECT LINE and MESSAGE BODY.''',

            'insufficient_enrichment': '''You are creating a strategic outreach message for 4Runr when we have limited lead enrichment data.

LEAD INFO:
- Name: {{ lead_data.Name }}
- Role: {{ lead_data.Title }}
- Company: {{ lead_data.Company }}

STRATEGY: Focus on universal business challenges and position 4Runr as having unique insights.

PROMPT TEMPLATE:
Hi {{first_name}},

Quick question: What's the biggest operational bottleneck you're dealing with right now?

We've been tracking patterns across hundreds of companies, and there are usually 2-3 hidden inefficiencies that most teams miss entirely.

Happy to share what we're seeing if it's relevant.

– 4Runr Team

REQUIREMENTS:
- Start with engaging question
- Reference our broad experience
- Create curiosity about insights
- Keep under 55 words
- Professional but conversational
- Soft value proposition

Generate SUBJECT LINE and MESSAGE BODY.''',

            'default': '''You are creating a bold, curiosity-driven outreach message for 4Runr when data quality is insufficient.

LEAD INFO:
- Name: {{ lead_data.Name }}
- Role: {{ lead_data.Title }}
- Company: {{ lead_data.Company }}

STRATEGY: Use scarcity and curiosity to create interest without relying on specific company data.

PROMPT TEMPLATE:
Hi {{first_name}},

We're only working with 3 new companies this quarter.

Not sure if {{company}} would be a fit, but the results we're seeing are pretty remarkable.

If you're curious about what's possible, let me know.

– 4Runr Team

REQUIREMENTS:
- Use scarcity (limited availability)
- Create curiosity about results
- Keep under 45 words
- Confident and exclusive tone
- No pressure, just opportunity
- Strong, memorable opening

Generate SUBJECT LINE and MESSAGE BODY.'''
        }
    
    async def _generate_fallback_message(self, state: CampaignState, prompt_template: str) -> CampaignMessage:
        """Generate a single fallback message using the selected prompt"""
        
        # Prepare template variables
        lead_data = state.lead_data
        first_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
        company = lead_data.get('Company', 'your company')
        
        # Render the prompt
        template = self.template_env.from_string(prompt_template)
        rendered_prompt = template.render(
            lead_data=lead_data,
            first_name=first_name,
            company=company
        )
        
        # Generate with OpenAI
        response = await self._call_openai(rendered_prompt)
        subject, body = self._parse_gpt_response(response)
        
        # Create message object
        message = CampaignMessage(
            message_type="fallback_hook",
            subject=subject,
            body=body,
            generation_attempt=1,
            quality_score=75.0,  # Assume good quality for fallback
            strategic_elements=["curiosity", "boldness", "scarcity"],
            tone_indicators=["confident", "intriguing"]
        )
        
        return message
    
    def _create_emergency_fallback(self, state: CampaignState) -> CampaignMessage:
        """Create an emergency fallback message if all generation fails"""
        
        lead_data = state.lead_data
        first_name = lead_data.get('Name', '').split()[0] if lead_data.get('Name') else 'there'
        company = lead_data.get('Company', 'your company')
        
        subject = "Quick question"
        body = f"""Hi {first_name},

We've been helping companies like {company} unlock hidden operational efficiencies.

Worth a brief conversation?

– 4Runr Team"""
        
        return CampaignMessage(
            message_type="emergency_fallback",
            subject=subject,
            body=body,
            generation_attempt=1,
            quality_score=60.0,
            strategic_elements=["simple", "direct"],
            tone_indicators=["professional", "brief"]
        )
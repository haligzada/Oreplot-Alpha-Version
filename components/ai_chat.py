"""
AI Chat Component for Oreplot
Provides conversational interface for highlighting important document points
and correcting AI analysis errors.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict
import os

AI_INTEGRATIONS_OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
AI_INTEGRATIONS_OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = bool(AI_INTEGRATIONS_OPENAI_API_KEY)
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = bool(AI_INTEGRATIONS_ANTHROPIC_API_KEY)
except ImportError:
    ANTHROPIC_AVAILABLE = False


def get_openai_client():
    """Get OpenAI client with Replit integration"""
    if not OPENAI_AVAILABLE:
        return None
    try:
        return OpenAI(
            api_key=AI_INTEGRATIONS_OPENAI_API_KEY,
            base_url=AI_INTEGRATIONS_OPENAI_BASE_URL
        )
    except Exception:
        return None


def get_anthropic_client():
    """Get Anthropic client with Replit integration"""
    if not ANTHROPIC_AVAILABLE:
        return None
    try:
        return Anthropic(
            api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
            base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
        )
    except Exception:
        return None


def init_chat_state(chat_key: str = "oreplot_chat"):
    """Initialize chat session state"""
    if f"{chat_key}_messages" not in st.session_state:
        st.session_state[f"{chat_key}_messages"] = []
    if f"{chat_key}_context" not in st.session_state:
        st.session_state[f"{chat_key}_context"] = {}


def add_message(chat_key: str, role: str, content: str):
    """Add a message to chat history"""
    if f"{chat_key}_messages" not in st.session_state:
        st.session_state[f"{chat_key}_messages"] = []
    
    st.session_state[f"{chat_key}_messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })


def set_context(chat_key: str, context: Dict):
    """Set context for AI understanding (uploaded files, analysis results, etc.)"""
    st.session_state[f"{chat_key}_context"] = context


def get_ai_response(chat_key: str, user_message: str, ai_tier: str = "light") -> str:
    """Generate AI response based on context and chat history"""
    
    context = st.session_state.get(f"{chat_key}_context", {})
    messages_history = st.session_state.get(f"{chat_key}_messages", [])
    
    uploaded_files = context.get("uploaded_files", [])
    extracted_text = context.get("extracted_text", "")
    analysis_result = context.get("analysis_result", {})
    project_name = context.get("project_name", "Mining Project")
    
    system_prompt = f"""You are Oreplot AI, an expert mining due diligence assistant. You help users analyze mining project documents and provide investment insights.

Current Project: {project_name}
Uploaded Files: {', '.join(uploaded_files) if uploaded_files else 'None yet'}

Your role:
1. Answer questions about the uploaded mining documents
2. Highlight and remember important points the user mentions about their project
3. If the user points out errors in your analysis, acknowledge them and provide corrected insights
4. Provide context-aware mining investment advice

Guidelines:
- Be concise but thorough
- Use mining industry terminology appropriately
- If you don't have enough information, ask for clarification
- When the user provides important context, confirm you've noted it
- If analysis results exist, you can reference and discuss them"""

    if extracted_text:
        system_prompt += f"\n\nExtracted Document Summary (first 3000 chars):\n{extracted_text[:3000]}"
    
    if analysis_result:
        if analysis_result.get('scoring'):
            score = analysis_result['scoring'].get('total_score', 'N/A')
            system_prompt += f"\n\nCurrent Analysis Score: {score}/100"
        if analysis_result.get('recommendations'):
            system_prompt += f"\n\nKey Recommendations: {', '.join(analysis_result['recommendations'][:3]) if isinstance(analysis_result['recommendations'], list) else str(analysis_result['recommendations'])[:500]}"
    
    conversation = []
    for msg in messages_history[-10:]:
        conversation.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    conversation.append({"role": "user", "content": user_message})
    
    if ai_tier == "advanced" and ANTHROPIC_AVAILABLE:
        client = get_anthropic_client()
        if client:
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=conversation
                )
                if response.content and hasattr(response.content[0], 'text'):
                    return response.content[0].text
                return "Unable to generate response."
            except Exception as e:
                pass
    
    if OPENAI_AVAILABLE:
        client = get_openai_client()
        if client:
            try:
                messages = [{"role": "system", "content": system_prompt}] + conversation
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,  # type: ignore
                    max_tokens=1024,
                    temperature=0.7
                )
                return response.choices[0].message.content or "No response generated."
            except Exception as e:
                return f"I'm having trouble connecting to the AI service. Please try again in a moment."
    
    return "AI service is not available. Please ensure API keys are configured."


def render_chat_interface(
    chat_key: str = "oreplot_chat",
    ai_tier: str = "light",
    placeholder_text: str = "Ask about your documents or highlight important points...",
    height: int = 300
):
    """
    Render the AI chat interface
    
    Args:
        chat_key: Unique key for this chat instance
        ai_tier: "light" or "advanced" for different AI models
        placeholder_text: Placeholder text for input
        height: Height of the chat container
    """
    
    init_chat_state(chat_key)
    
    tier_color = "#8B5CF6" if ai_tier == "advanced" else "#3B82F6"
    tier_name = "Advanced AI" if ai_tier == "advanced" else "Light AI"
    
    st.markdown(f"""
        <style>
            .chat-container {{
                background: #FAFAFA;
                border-radius: 12px;
                padding: 16px;
                margin: 10px 0;
                border: 1px solid #E5E7EB;
            }}
            .chat-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 12px;
                padding-bottom: 12px;
                border-bottom: 1px solid #E5E7EB;
            }}
            .chat-badge {{
                background: {tier_color};
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
            }}
            .message-user {{
                background: {tier_color};
                color: white;
                padding: 10px 14px;
                border-radius: 16px 16px 4px 16px;
                margin: 8px 0;
                margin-left: 40px;
                font-size: 0.9rem;
            }}
            .message-assistant {{
                background: white;
                color: #1F2937;
                padding: 10px 14px;
                border-radius: 16px 16px 16px 4px;
                margin: 8px 0;
                margin-right: 40px;
                border: 1px solid #E5E7EB;
                font-size: 0.9rem;
            }}
            .chat-messages {{
                max-height: {height}px;
                overflow-y: auto;
                padding: 8px 0;
            }}
            .empty-chat {{
                text-align: center;
                color: #9CA3AF;
                padding: 20px;
                font-size: 0.9rem;
            }}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="chat-container">
            <div class="chat-header">
                <span style="font-weight: 600; color: #1F2937;">💬 Chat with Oreplot AI</span>
                <span class="chat-badge">{tier_name}</span>
            </div>
    """, unsafe_allow_html=True)
    
    messages = st.session_state.get(f"{chat_key}_messages", [])
    
    if messages:
        messages_html = '<div class="chat-messages">'
        for msg in messages[-20:]:
            if msg["role"] == "user":
                messages_html += f'<div class="message-user">{msg["content"]}</div>'
            else:
                messages_html += f'<div class="message-assistant">{msg["content"]}</div>'
        messages_html += '</div>'
        st.markdown(messages_html, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="empty-chat">
                <div style="font-size: 1.5rem; margin-bottom: 8px;">💡</div>
                <div>Share important details about your project or ask questions about your documents</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.form(key=f"{chat_key}_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder=placeholder_text,
                key=f"{chat_key}_input",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.form_submit_button("Send", type="primary", use_container_width=True)
        
        if send_button and user_input and user_input.strip():
            add_message(chat_key, "user", user_input.strip())
            
            with st.spinner("Thinking..."):
                response = get_ai_response(chat_key, user_input.strip(), ai_tier)
                add_message(chat_key, "assistant", response)
            
            st.rerun()


def render_compact_chat_input(
    chat_key: str = "oreplot_chat",
    ai_tier: str = "light",
    placeholder_text: str = "Highlight important points about your documents..."
):
    """
    Render a compact chat with message history and input field
    Used during document upload phase
    """
    
    init_chat_state(chat_key)
    
    tier_color = "#8B5CF6" if ai_tier == "advanced" else "#3B82F6"
    tier_name = "Advanced AI" if ai_tier == "advanced" else "Light AI"
    
    st.markdown(f"""
        <style>
            .compact-chat-container {{
                background: #F9FAFB;
                border-radius: 12px;
                padding: 14px;
                margin: 10px 0;
                border: 1px solid #E5E7EB;
            }}
            .compact-chat-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 10px;
            }}
            .compact-badge {{
                background: {tier_color};
                color: white;
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 0.7rem;
                font-weight: 600;
            }}
            .compact-messages {{
                max-height: 200px;
                overflow-y: auto;
                margin-bottom: 10px;
            }}
            .compact-msg-user {{
                background: {tier_color};
                color: white;
                padding: 8px 12px;
                border-radius: 14px 14px 4px 14px;
                margin: 6px 0;
                margin-left: 30px;
                font-size: 0.85rem;
            }}
            .compact-msg-ai {{
                background: white;
                color: #1F2937;
                padding: 8px 12px;
                border-radius: 14px 14px 14px 4px;
                margin: 6px 0;
                margin-right: 30px;
                border: 1px solid #E5E7EB;
                font-size: 0.85rem;
            }}
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="compact-chat-container">
            <div class="compact-chat-header">
                <span style="color: {tier_color}; font-weight: 600;">💬 Chat with Oreplot AI</span>
                <span class="compact-badge">{tier_name}</span>
            </div>
    """, unsafe_allow_html=True)
    
    messages = st.session_state.get(f"{chat_key}_messages", [])
    
    if messages:
        messages_html = '<div class="compact-messages">'
        for msg in messages[-10:]:
            if msg["role"] == "user":
                messages_html += f'<div class="compact-msg-user">{msg["content"]}</div>'
            else:
                messages_html += f'<div class="compact-msg-ai">{msg["content"]}</div>'
        messages_html += '</div>'
        st.markdown(messages_html, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.form(key=f"{chat_key}_compact_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder=placeholder_text,
                key=f"{chat_key}_compact_input",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.form_submit_button("Send", type="primary", use_container_width=True)
        
        if send_button and user_input and user_input.strip():
            add_message(chat_key, "user", user_input.strip())
            
            with st.spinner("Thinking..."):
                response = get_ai_response(chat_key, user_input.strip(), ai_tier)
                add_message(chat_key, "assistant", response)
            
            st.rerun()


def clear_chat(chat_key: str = "oreplot_chat"):
    """Clear chat history"""
    if f"{chat_key}_messages" in st.session_state:
        st.session_state[f"{chat_key}_messages"] = []
    if f"{chat_key}_context" in st.session_state:
        st.session_state[f"{chat_key}_context"] = {}

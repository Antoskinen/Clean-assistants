import os
import streamlit as st
import openai
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 🔑 PREDEFINED CREDENTIALS 
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('Interreg_assistant')


# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Page configuration
st.set_page_config(page_title="Interreg Assistant", page_icon="🤖", layout="wide")

# Initialize session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Utility Functions
def create_thread() -> str:
    """Create a new conversation thread"""
    try:
        thread = openai.beta.threads.create()
        return thread.id
    except Exception as e:
        st.error(f"Error creating thread: {e}")
        return None

def add_message_to_thread(thread_id: str, content: str) -> dict:
    """Add a user message to the thread"""
    try:
        message = openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content
        )
        return message
    except Exception as e:
        st.error(f"Error adding message: {e}")
        return None

def run_assistant(thread_id: str) -> str:
    """Run the assistant and retrieve the response"""
    try:
        # Create a run
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        # Wait for run completion
        while run.status != "completed":
            run = openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            time.sleep(1)  # Polling interval
            
            # Handle potential errors
            if run.status == "failed":
                st.error("Assistant run failed.")
                return None
        
        # Retrieve messages
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        
        # Get the latest assistant message
        for msg in messages.data:
            if msg.role == "assistant":
                # Extract text from the first content block (assuming text)
                return msg.content[0].text.value
        
        return "No response from assistant"
    
    except Exception as e:
        st.error(f"Error running assistant: {e}")
        return None

# Main App Interface
st.title("🤖 Interreg Assistant")

# Optional sidebar for additional controls
with st.sidebar:
    st.header("🛠 Assistant Controls")
    # Temperature Slider
    temperature = st.slider("👨‍🎨 Creativity/Randomness", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
    create_thread_btn = st.button("🔄 Reset Conversation")
    

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to ask your assistant?"):
    # Create thread if not exists
    if not st.session_state.thread_id:
        st.session_state.thread_id = create_thread()
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to thread and session
    st.session_state.messages.append({"role": "user", "content": prompt})
    add_message_to_thread(st.session_state.thread_id, prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking...🤔"):
            response = run_assistant(st.session_state.thread_id)
            
            # Display and store response
            if response:
                st.markdown(response)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })

# Create New Thread Button in Sidebar
if create_thread_btn:
    # Reset conversation
    st.session_state.thread_id = create_thread()
    st.session_state.messages = []
    st.success("🔄 Conversation reset!")

# Footer
st.markdown("---")
st.markdown("*Powered by Anton, Streamlit & OpenAI, and also a shoutout ot Claude*") 
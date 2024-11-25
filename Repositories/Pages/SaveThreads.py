import os
import json
import streamlit as st
import openai
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 🔑 PREDEFINED CREDENTIALS 
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('Ecosystem_assistant')

# Threads Storage Directory
THREADS_DIR = 'saved_threads'
os.makedirs(THREADS_DIR, exist_ok=True)

class ThreadManager:
    @staticmethod
    def save_thread(thread_id, messages):
        """Save thread messages to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(THREADS_DIR, f"thread_{timestamp}.json")
        
        thread_data = {
            "thread_id": thread_id,
            "timestamp": timestamp,
            "messages": messages
        }
        
        with open(filename, 'w') as f:
            json.dump(thread_data, f, indent=4)
        
        st.toast(f"Thread saved: {filename}")
    
    @staticmethod
    def list_saved_threads():
        """List all saved thread files"""
        return sorted(
            [f for f in os.listdir(THREADS_DIR) if f.endswith('.json')], 
            reverse=True
        )
    
    @staticmethod
    def load_thread(filename):
        """Load a specific thread from a file"""
        filepath = os.path.join(THREADS_DIR, filename)
        with open(filepath, 'r') as f:
            return json.load(f)

# OpenAI Configuration
openai.api_key = OPENAI_API_KEY

# Streamlit Page Configuration
st.set_page_config(page_title="Ecosystem Assistant", page_icon="🤖", layout="wide")

# Initialize Session State
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Thread Management
with st.sidebar:
    st.header("🛠 Thread Management")
    
    # Temperature Slider
    temperature = st.slider("👨‍🎨 Creativity/Randomness", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
    # Clear thread
    create_thread_btn = st.button("🔄 Reset Conversation")

    # Save Current Thread Button
    if st.button("💾 Save Current Thread"):
        if st.session_state.messages:
            ThreadManager.save_thread(
                st.session_state.thread_id, 
                st.session_state.messages
            )
        else:
            st.warning("No messages to save!")
    
    # Saved Threads Section
    st.subheader("Saved Threads")
    saved_threads = ThreadManager.list_saved_threads()
    
    # Dropdown to select and load saved threads
    if saved_threads:
        selected_thread = st.selectbox(
            "Select a saved thread", 
            saved_threads
        )
        
        # Load Thread Button
        if st.button("🔍 Load Selected Thread"):
            try:
                loaded_thread = ThreadManager.load_thread(selected_thread)
                st.session_state.messages = loaded_thread['messages']
                st.success(f"Loaded thread from {selected_thread}")
            except Exception as e:
                st.error(f"Error loading thread: {e}")
    else:
        st.info("No saved threads yet.")

# Utility Functions (Keep existing create_thread, add_message_to_thread, run_assistant functions from previous implementation)
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
st.title("🤖 Ecosystem Assistant")

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
        with st.spinner("Thinking..."):
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
st.markdown("*Powered by Streamlit, OpenAI Assistants API & Thread Saving*")
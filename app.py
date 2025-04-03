import streamlit as st
import pandas as pd
import datetime
import os
from memory_processor import (
    process_memory,
    generate_memory_embedding,
    recall_memories,
    summarize_memories,
    analyze_emotion,
    openai_available  # Import flag that indicates if OpenAI API is working
)
from data_store import (
    save_memory,
    load_memories,
    get_memory_by_id,
    update_memory_unlock_date
)
from visualizer import generate_mind_map
from voice_input import transcribe_voice
from utils import get_current_date

# Page configuration
st.set_page_config(
    page_title="MemoryVault AI",
    page_icon="💾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if "memories" not in st.session_state:
    st.session_state.memories = load_memories()
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Capture"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "filter_emotion" not in st.session_state:
    st.session_state.filter_emotion = "All"
if "filter_person" not in st.session_state:
    st.session_state.filter_person = "All"
if "filter_date_range" not in st.session_state:
    st.session_state.filter_date_range = (None, None)
if "time_capsule_date" not in st.session_state:
    st.session_state.time_capsule_date = None

# Custom CSS styles
st.markdown("""
    <style>
    .main-header {
        font-size: 42px;
        font-weight: bold;
        color: #6c5ce7;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 24px;
        font-weight: bold;
        color: #2d3436;
        margin-bottom: 10px;
    }
    .memory-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #6c5ce7;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .memory-date {
        color: #7f8c8d;
        font-size: 14px;
    }
    .memory-emotion {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        margin-right: 5px;
    }
    .memory-people {
        color: #3498db;
        font-weight: bold;
    }
    .memory-location {
        color: #2ecc71;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown("<div class='main-header'>💾 MemoryVault AI</div>", unsafe_allow_html=True)
st.markdown("### Your Digital Brain for Life Moments")

# Sidebar
st.sidebar.image("icon.svg", width=50)
st.sidebar.title("MemoryVault AI")

# Check for OpenAI API key and availability
import os
if not os.environ.get("OPENAI_API_KEY"):
    st.sidebar.warning("""
    ⚠️ **API Key Required** 
    
    This app needs an OpenAI API key. Some features use fallback methods when the API is unavailable.
    """)
elif not openai_available:
    st.sidebar.warning("""
    ⚠️ **OpenAI API Connection Issue** 
    
    There's a problem connecting to the OpenAI API. The app will use fallback methods.
    """)
else:
    st.sidebar.success("""
    ✅ **OpenAI API Connected** 
    
    The app is using OpenAI's AI capabilities for enhanced features.
    """)

# Navigation
tab_options = ["Capture", "Recall", "Mind Map", "Time Capsule", "Summaries"]
st.session_state.active_tab = st.sidebar.radio("Navigation", tab_options)

# User info
st.sidebar.markdown("---")
st.sidebar.markdown("### Your Memory Stats")
if st.session_state.memories:
    st.sidebar.metric("Total Memories", len(st.session_state.memories))
    emotions = [memory.get('emotion', 'Unknown') for memory in st.session_state.memories]
    most_common_emotion = max(set(emotions), key=emotions.count)
    st.sidebar.metric("Most Common Emotion", most_common_emotion)
    
    # Calculate locked memories (time capsules)
    current_date = get_current_date()
    locked_memories = [m for m in st.session_state.memories if m.get('unlock_date') and m.get('unlock_date') > current_date]
    st.sidebar.metric("Time Capsules", len(locked_memories))
else:
    st.sidebar.write("No memories stored yet.")

st.sidebar.markdown("---")
st.sidebar.info("MemoryVault AI helps you store and recall life moments with the power of AI.")

# Main content based on active tab
if st.session_state.active_tab == "Capture":
    st.markdown("<div class='sub-header'>📝 Capture New Memory</div>", unsafe_allow_html=True)
    
    # Memory input options
    input_method = st.radio("Choose input method:", ["Text", "Voice"])
    
    memory_text = ""
    if input_method == "Text":
        memory_text = st.text_area("Enter your memory:", height=150,
                                   placeholder="What would you like to remember? Share your thoughts, ideas, or experiences...")
    else:  # Voice input
        memory_text = transcribe_voice()
        if memory_text:
            st.success("Voice captured successfully!")
            st.write(f"**Transcribed text:** {memory_text}")
    
    # Additional memory metadata
    col1, col2 = st.columns(2)
    with col1:
        people_involved = st.text_input("People involved (comma separated):", 
                                        placeholder="e.g., John, Lisa, Mom")
    with col2:
        location = st.text_input("Location:", placeholder="e.g., Home, Coffee shop, Park")
    
    # Time capsule option
    time_capsule = st.checkbox("Make this a time capsule memory")
    unlock_date = None
    if time_capsule:
        min_date = datetime.date.today() + datetime.timedelta(days=1)
        unlock_date = st.date_input("When should this memory be unlocked?", 
                                    min_value=min_date,
                                    value=min_date + datetime.timedelta(days=30))
    
    # Save memory
    if st.button("Save Memory"):
        if memory_text:
            with st.spinner("Processing your memory..."):
                # Display API notice
                st.info("Analyzing your memory with AI... If the OpenAI API quota is exceeded, we'll use basic text analysis instead.")
                
                # Process the memory with AI
                processed_memory = process_memory(memory_text)
                
                # Extract relevant information
                emotion = processed_memory.get('emotion', 'Neutral')
                topics = processed_memory.get('topics', [])
                context = processed_memory.get('context', '')
                
                # Create people list from input
                people = [p.strip() for p in people_involved.split(',')] if people_involved else []
                
                # Generate embedding for similarity search
                embedding = generate_memory_embedding(memory_text)
                
                # Create memory object
                memory = {
                    'id': len(st.session_state.memories) + 1,
                    'text': memory_text,
                    'date': get_current_date(),
                    'emotion': emotion,
                    'people': people,
                    'location': location if location else 'Unknown',
                    'topics': topics,
                    'context': context,
                    'embedding': embedding,
                    'unlock_date': unlock_date.isoformat() if unlock_date else None
                }
                
                # Save to storage
                save_memory(memory)
                
                # Update session state
                st.session_state.memories = load_memories()
                
                st.success("Memory saved successfully!")
                st.json(memory)
        else:
            st.error("Please enter a memory before saving.")

elif st.session_state.active_tab == "Recall":
    st.markdown("<div class='sub-header'>🔍 Recall Memories</div>", unsafe_allow_html=True)
    
    # Search and filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Search for memories:", 
                                    placeholder="Ask a question or search by keyword...")
    with col2:
        search_button = st.button("Search")
    
    # Filters
    st.write("Filter options:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get unique emotions from memories
        all_emotions = set()
        for memory in st.session_state.memories:
            all_emotions.add(memory.get('emotion', 'Unknown'))
        emotion_filter = st.selectbox("Filter by emotion:", ["All"] + sorted(list(all_emotions)))
    
    with col2:
        # Get unique people from memories
        all_people = set()
        for memory in st.session_state.memories:
            for person in memory.get('people', []):
                all_people.add(person)
        person_filter = st.selectbox("Filter by person:", ["All"] + sorted(list(all_people)))
    
    with col3:
        date_range = st.date_input("Date range:",
                                  value=[datetime.date.today() - datetime.timedelta(days=30), 
                                         datetime.date.today()],
                                  max_value=datetime.date.today())
    
    # Search logic
    filtered_memories = []
    if search_query and search_button:
        with st.spinner("Searching memories..."):
            # Use AI to recall memories based on the query
            recalled_memories = recall_memories(search_query, st.session_state.memories)
            st.write(f"Found {len(recalled_memories)} relevant memories:")
            filtered_memories = recalled_memories
    else:
        # Apply filters
        current_date = get_current_date()
        filtered_memories = st.session_state.memories
        
        # Filter unlocked memories
        filtered_memories = [m for m in filtered_memories 
                            if not m.get('unlock_date') or m.get('unlock_date') <= current_date]
        
        # Apply emotion filter
        if emotion_filter != "All":
            filtered_memories = [m for m in filtered_memories if m.get('emotion') == emotion_filter]
        
        # Apply person filter
        if person_filter != "All":
            filtered_memories = [m for m in filtered_memories if person_filter in m.get('people', [])]
        
        # Apply date filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_memories = [
                m for m in filtered_memories
                if start_date.isoformat() <= m.get('date')[:10] <= end_date.isoformat()
            ]
    
    # Display filtered memories
    if filtered_memories:
        for memory in filtered_memories:
            with st.container():
                st.markdown(f"""
                <div class='memory-card'>
                    <div class='memory-date'>{memory.get('date')}</div>
                    <p>{memory.get('text')}</p>
                    <span class='memory-emotion' style='background-color: {"#ff7675" if memory.get("emotion") in ["Angry", "Sad", "Frustrated"] else "#74b9ff" if memory.get("emotion") in ["Happy", "Excited", "Joyful"] else "#81ecec"};'>
                        {memory.get('emotion', 'Unknown')}
                    </span>
                    {f"<span class='memory-people'>With: {', '.join(memory.get('people', []))}</span>" if memory.get('people') else ""}
                    {f"<span class='memory-location'>@ {memory.get('location')}</span>" if memory.get('location') and memory.get('location') != 'Unknown' else ""}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No memories found with the current filters. Try adjusting your search parameters.")

elif st.session_state.active_tab == "Mind Map":
    st.markdown("<div class='sub-header'>🧠 Memory Mind Map</div>", unsafe_allow_html=True)
    
    if st.session_state.memories:
        # Get unlocked memories
        current_date = get_current_date()
        available_memories = [m for m in st.session_state.memories 
                             if not m.get('unlock_date') or m.get('unlock_date') <= current_date]
        
        if available_memories:
            # Generate and display mind map
            with st.spinner("Generating mind map..."):
                mind_map_fig = generate_mind_map(available_memories)
                st.plotly_chart(mind_map_fig, use_container_width=True)
                
            # Display memory connections explanation
            st.markdown("### Understanding Your Memory Connections")
            st.write("""
            This mind map visualizes how your memories are connected through:
            - **Common topics** (blue lines)
            - **People** (orange lines)
            - **Emotions** (green lines)
            - **Locations** (purple lines)
            
            The size of each node represents how many connections that memory has to other memories.
            """)
        else:
            st.info("No available memories to visualize. Memories set as time capsules will appear here once unlocked.")
    else:
        st.info("No memories stored yet. Add some memories to see your mind map.")

elif st.session_state.active_tab == "Time Capsule":
    st.markdown("<div class='sub-header'>⏰ Time Capsule Memories</div>", unsafe_allow_html=True)
    
    # Create new time capsule section
    st.markdown("### Create a New Time Capsule")
    time_capsule_text = st.text_area("Write a message to your future self:", height=150,
                                   placeholder="What would you like to tell your future self?")
    
    # Time capsule metadata
    col1, col2 = st.columns(2)
    with col1:
        min_date = datetime.date.today() + datetime.timedelta(days=1)
        capsule_unlock_date = st.date_input("When should this capsule be unlocked?", 
                                          min_value=min_date,
                                          value=min_date + datetime.timedelta(days=365))
    with col2:
        capsule_emotion = st.selectbox("How are you feeling now?", 
                                     ["Happy", "Excited", "Nostalgic", "Hopeful", "Anxious", 
                                      "Curious", "Peaceful", "Grateful", "Reflective"])
    
    if st.button("Create Time Capsule"):
        if time_capsule_text:
            with st.spinner("Creating your time capsule..."):
                # Process the memory
                processed_memory = process_memory(time_capsule_text)
                topics = processed_memory.get('topics', [])
                context = processed_memory.get('context', '')
                
                # Generate embedding
                embedding = generate_memory_embedding(time_capsule_text)
                
                # Create memory object
                memory = {
                    'id': len(st.session_state.memories) + 1,
                    'text': time_capsule_text,
                    'date': get_current_date(),
                    'emotion': capsule_emotion,
                    'people': [],
                    'location': 'Time Capsule',
                    'topics': topics,
                    'context': context,
                    'embedding': embedding,
                    'unlock_date': capsule_unlock_date.isoformat(),
                    'is_time_capsule': True
                }
                
                # Save to storage
                save_memory(memory)
                
                # Update session state
                st.session_state.memories = load_memories()
                
                st.success(f"Time capsule created! It will be unlocked on {capsule_unlock_date.strftime('%B %d, %Y')}.")
        else:
            st.error("Please enter a message before creating a time capsule.")
    
    # Display time capsules
    st.markdown("---")
    st.markdown("### Your Time Capsules")
    
    # Filter for time capsule memories
    time_capsules = [m for m in st.session_state.memories if m.get('unlock_date')]
    
    if time_capsules:
        # Sort by unlock date
        time_capsules.sort(key=lambda x: x.get('unlock_date'))
        
        # Group into locked and unlocked
        current_date = get_current_date()
        locked_capsules = [tc for tc in time_capsules if tc.get('unlock_date') > current_date]
        unlocked_capsules = [tc for tc in time_capsules if tc.get('unlock_date') <= current_date]
        
        # Display locked capsules
        if locked_capsules:
            st.markdown("#### 🔒 Locked Time Capsules")
            for capsule in locked_capsules:
                unlock_date = datetime.datetime.fromisoformat(capsule.get('unlock_date')).date()
                days_until_unlock = (unlock_date - datetime.date.today()).days
                
                with st.container():
                    st.markdown(f"""
                    <div class='memory-card' style='border-left: 5px solid #ffeaa7;'>
                        <div class='memory-date'>Created on: {capsule.get('date')[:10]}</div>
                        <div class='memory-date'>Unlocks in: {days_until_unlock} days ({unlock_date.strftime('%B %d, %Y')})</div>
                        <p>This time capsule is locked until the unlock date.</p>
                        <span class='memory-emotion' style='background-color: #ffeaa7;'>
                            {capsule.get('emotion', 'Unknown')}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Display unlocked capsules
        if unlocked_capsules:
            st.markdown("#### 🔓 Unlocked Time Capsules")
            for capsule in unlocked_capsules:
                with st.container():
                    st.markdown(f"""
                    <div class='memory-card' style='border-left: 5px solid #55efc4;'>
                        <div class='memory-date'>Created on: {capsule.get('date')[:10]}</div>
                        <div class='memory-date'>Unlocked on: {capsule.get('unlock_date')}</div>
                        <p>{capsule.get('text')}</p>
                        <span class='memory-emotion' style='background-color: #55efc4;'>
                            {capsule.get('emotion', 'Unknown')}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("You don't have any time capsules yet. Create one to leave a message for your future self!")

elif st.session_state.active_tab == "Summaries":
    st.markdown("<div class='sub-header'>📊 Memory Summaries</div>", unsafe_allow_html=True)
    
    if st.session_state.memories:
        # Get unlocked memories
        current_date = get_current_date()
        available_memories = [m for m in st.session_state.memories 
                             if not m.get('unlock_date') or m.get('unlock_date') <= current_date]
        
        if available_memories:
            # Time period selection
            summary_period = st.selectbox(
                "Generate summary for:",
                ["Past Week", "Past Month", "Past 3 Months", "Past Year", "All Time"]
            )
            
            if st.button("Generate Summary"):
                with st.spinner("Analyzing your memories..."):
                    # Filter memories based on selected time period
                    today = datetime.date.today()
                    
                    if summary_period == "Past Week":
                        start_date = (today - datetime.timedelta(days=7)).isoformat()
                    elif summary_period == "Past Month":
                        start_date = (today - datetime.timedelta(days=30)).isoformat()
                    elif summary_period == "Past 3 Months":
                        start_date = (today - datetime.timedelta(days=90)).isoformat()
                    elif summary_period == "Past Year":
                        start_date = (today - datetime.timedelta(days=365)).isoformat()
                    else:  # All Time
                        start_date = "1900-01-01"  # Very early date to include everything
                    
                    filtered_memories = [
                        m for m in available_memories
                        if m.get('date')[:10] >= start_date
                    ]
                    
                    if filtered_memories:
                        # Generate summary
                        summary = summarize_memories(filtered_memories, summary_period)
                        
                        # Display summary
                        st.markdown(f"### Summary for {summary_period}")
                        st.markdown(summary)
                        
                        # Emotion analysis
                        emotions = [m.get('emotion', 'Unknown') for m in filtered_memories]
                        emotion_counts = {}
                        for emotion in emotions:
                            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                        
                        # Create emotion chart
                        emotion_df = pd.DataFrame({
                            'Emotion': list(emotion_counts.keys()),
                            'Count': list(emotion_counts.values())
                        })
                        emotion_df = emotion_df.sort_values('Count', ascending=False)
                        
                        st.markdown("### Emotion Distribution")
                        st.bar_chart(emotion_df.set_index('Emotion'))
                        
                        # People mentioned
                        people_counts = {}
                        for memory in filtered_memories:
                            for person in memory.get('people', []):
                                people_counts[person] = people_counts.get(person, 0) + 1
                        
                        if people_counts:
                            people_df = pd.DataFrame({
                                'Person': list(people_counts.keys()),
                                'Mentions': list(people_counts.values())
                            })
                            people_df = people_df.sort_values('Mentions', ascending=False).head(10)
                            
                            st.markdown("### Most Mentioned People")
                            st.bar_chart(people_df.set_index('Person'))
                    else:
                        st.info(f"No memories found for the {summary_period} period.")
        else:
            st.info("No available memories to summarize. Memories set as time capsules will be included once unlocked.")
    else:
        st.info("No memories stored yet. Add some memories to generate summaries.")

# Footer
st.markdown("---")
st.markdown("MemoryVault AI - Your personal memory assistant powered by AI")

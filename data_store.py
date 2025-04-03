import os
import json
import pickle
from datetime import datetime
import streamlit as st

# Constants
DATA_DIRECTORY = "data"
MEMORIES_FILE = "memories.pkl"

def ensure_data_directory():
    """Ensure the data directory exists"""
    os.makedirs(DATA_DIRECTORY, exist_ok=True)

def get_data_file_path():
    """Get the full path to the memories data file"""
    ensure_data_directory()
    return os.path.join(DATA_DIRECTORY, MEMORIES_FILE)

def save_memory(memory):
    """
    Save a new memory to storage.
    
    Args:
        memory (dict): The memory object to save
    """
    # Load existing memories
    memories = load_memories()
    
    # Add the new memory
    memories.append(memory)
    
    # Update the session state
    st.session_state.memories = memories
    
    # Save to disk
    try:
        with open(get_data_file_path(), 'wb') as f:
            pickle.dump(memories, f)
    except Exception as e:
        st.error(f"Failed to save memory: {e}")

def load_memories():
    """
    Load all memories from storage.
    
    Returns:
        list: List of memory objects
    """
    try:
        if os.path.exists(get_data_file_path()):
            with open(get_data_file_path(), 'rb') as f:
                return pickle.load(f)
        else:
            return []
    except Exception as e:
        st.error(f"Failed to load memories: {e}")
        return []

def get_memory_by_id(memory_id):
    """
    Get a specific memory by its ID.
    
    Args:
        memory_id (int): The ID of the memory to retrieve
        
    Returns:
        dict: The memory object if found, None otherwise
    """
    memories = load_memories()
    for memory in memories:
        if memory.get('id') == memory_id:
            return memory
    return None

def update_memory(memory_id, updated_data):
    """
    Update an existing memory.
    
    Args:
        memory_id (int): The ID of the memory to update
        updated_data (dict): The updated memory data
        
    Returns:
        bool: True if successful, False otherwise
    """
    memories = load_memories()
    for i, memory in enumerate(memories):
        if memory.get('id') == memory_id:
            # Update the memory with new data
            memories[i].update(updated_data)
            
            # Save changes
            with open(get_data_file_path(), 'wb') as f:
                pickle.dump(memories, f)
            
            # Update session state
            st.session_state.memories = memories
            
            return True
    
    return False

def update_memory_unlock_date(memory_id, new_unlock_date):
    """
    Update the unlock date of a time capsule memory.
    
    Args:
        memory_id (int): The ID of the memory to update
        new_unlock_date (str): The new unlock date as ISO format string
        
    Returns:
        bool: True if successful, False otherwise
    """
    return update_memory(memory_id, {'unlock_date': new_unlock_date})

def delete_memory(memory_id):
    """
    Delete a memory by its ID.
    
    Args:
        memory_id (int): The ID of the memory to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    memories = load_memories()
    for i, memory in enumerate(memories):
        if memory.get('id') == memory_id:
            # Remove the memory
            del memories[i]
            
            # Save changes
            with open(get_data_file_path(), 'wb') as f:
                pickle.dump(memories, f)
            
            # Update session state
            st.session_state.memories = memories
            
            return True
    
    return False

def export_memories_json():
    """
    Export all memories as a JSON string for backup or transfer.
    
    Returns:
        str: JSON string of all memories
    """
    memories = load_memories()
    
    # Create serializable version (remove embeddings)
    serializable_memories = []
    for memory in memories:
        mem_copy = memory.copy()
        # Remove embedding vectors as they're not easily serializable
        if 'embedding' in mem_copy:
            del mem_copy['embedding']
        serializable_memories.append(mem_copy)
    
    return json.dumps(serializable_memories, indent=2)

def import_memories_json(json_str):
    """
    Import memories from a JSON string.
    
    Args:
        json_str (str): JSON string containing memories
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        imported_memories = json.loads(json_str)
        
        # Get existing memories
        current_memories = load_memories()
        
        # Generate new IDs for imported memories to avoid conflicts
        next_id = max([m.get('id', 0) for m in current_memories], default=0) + 1
        
        # Process each imported memory
        for memory in imported_memories:
            # Assign new ID
            memory['id'] = next_id
            next_id += 1
            
            # Add to existing memories
            current_memories.append(memory)
        
        # Save combined memories
        with open(get_data_file_path(), 'wb') as f:
            pickle.dump(current_memories, f)
        
        # Update session state
        st.session_state.memories = current_memories
        
        return True
    except Exception as e:
        st.error(f"Failed to import memories: {e}")
        return False

import os
from openai import OpenAI
import json

# Initialize OpenAI client with error handling
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Flag to track if OpenAI is available
openai_available = False
client = None

try:
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
        # Test with a simple request to verify the API key works
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        openai_available = True
        print("OpenAI API connection successful!")
except Exception as e:
    print(f"OpenAI initialization error: {e}")
    # If there's an insufficient_quota error, that means the key is valid but has no credits
    if "insufficient_quota" in str(e):
        print("API key is valid but has insufficient quota. Using fallback methods.")
    # We'll use fallback methods when OpenAI is not available

def process_memory(text):
    """
    Process a new memory using OpenAI to extract context, emotion, topics, etc.
    
    Args:
        text (str): The memory text to process
        
    Returns:
        dict: Processed memory with contextual information
    """
    # Simple text analysis without API for basic emotion detection
    def basic_emotion_analysis(txt):
        txt = txt.lower()
        emotions = {
            'Happy': ['happy', 'joy', 'excited', 'glad', 'delighted', 'pleased'],
            'Sad': ['sad', 'unhappy', 'depressed', 'down', 'blue', 'upset'],
            'Angry': ['angry', 'mad', 'furious', 'annoyed', 'irritated'],
            'Anxious': ['anxious', 'worried', 'nervous', 'stressed'],
            'Peaceful': ['peaceful', 'calm', 'relaxed', 'tranquil'],
            'Nostalgic': ['nostalgic', 'remember', 'memory', 'past', 'childhood'],
            'Grateful': ['grateful', 'thankful', 'appreciate']
        }
        
        # Count emotion word occurrences
        emotion_scores = {emotion: 0 for emotion in emotions}
        for emotion, keywords in emotions.items():
            for keyword in keywords:
                if keyword in txt:
                    emotion_scores[emotion] += 1
        
        # Get the dominant emotion or default to Neutral
        if any(emotion_scores.values()):
            dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            return dominant_emotion
        return 'Neutral'
    
    # Basic topic extraction without API
    def basic_topic_extraction(txt):
        common_topics = [
            'family', 'work', 'school', 'friends', 'travel', 'food', 'health', 
            'hobby', 'achievement', 'challenge', 'celebration', 'learning'
        ]
        
        found_topics = []
        txt_lower = txt.lower()
        for topic in common_topics:
            if topic in txt_lower:
                found_topics.append(topic.capitalize())
        
        return found_topics[:3]  # Limit to top 3 topics
    
    # Try to use the API first
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at analyzing personal memories and extracting relevant information. "
                    "Given a personal memory text, identify the emotional tone, key topics, people mentioned, "
                    "potential locations, and provide broader context to the memory. "
                    "Respond with a JSON object."
                },
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"},
        )
        
        # Parse the JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Ensure we have the expected fields
        processed_memory = {
            'emotion': result.get('emotion', 'Neutral'),
            'topics': result.get('topics', []),
            'context': result.get('context', ''),
            'people_mentioned': result.get('people_mentioned', []),
            'location': result.get('location', 'Unknown')
        }
        
        return processed_memory
    
    except Exception as e:
        print(f"Error processing memory: {e}")
        # Use fallback basic analysis
        emotion = basic_emotion_analysis(text)
        topics = basic_topic_extraction(text)
        
        # Look for location mentions
        location_keywords = ['at', 'in', 'near', 'by']
        location = 'Unknown'
        for keyword in location_keywords:
            if f" {keyword} " in f" {text} ":
                parts = text.split(f" {keyword} ")
                if len(parts) > 1:
                    possible_location = parts[1].split('.')[0].split(',')[0]
                    if len(possible_location) < 30:  # Reasonable location name length
                        location = possible_location
                        break
        
        # Return processed memory with basic analysis
        return {
            'emotion': emotion,
            'topics': topics,
            'context': f"This memory appears to be about {', '.join(topics)}" if topics else "",
            'people_mentioned': [],
            'location': location
        }

def generate_memory_embedding(text):
    """
    Generate an embedding for the memory text for semantic search.
    
    Args:
        text (str): The memory text to embed
        
    Returns:
        list: Vector embedding of the memory text
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Generate a simple hash-based pseudo-embedding as fallback
        # This is not as effective as real embeddings but provides something to work with
        import hashlib
        
        # Create a simple pseudo-embedding based on text characteristics
        words = text.lower().split()
        # Use a hash to generate a stable but unique number for each word
        word_hashes = [int(hashlib.md5(word.encode()).hexdigest(), 16) for word in words if word]
        
        # Create a very basic 10-dimensional embedding from the hash values
        if word_hashes:
            pseudo_embedding = []
            for i in range(10):  # 10-dimensional pseudo-embedding
                # Use different slices of the hash values for each dimension
                values = [h % (100 + i * 10) for h in word_hashes]
                # Average the values and normalize to range [-1, 1]
                pseudo_embedding.append((sum(values) / len(values) / 100) * 2 - 1)
            
            # Pad to length 10
            while len(pseudo_embedding) < 10:
                pseudo_embedding.append(0.0)
                
            return pseudo_embedding
            
        # If no words, return zeros
        return [0.0] * 10

def recall_memories(query, memories):
    """
    Use AI to recall memories based on a natural language query.
    
    Args:
        query (str): The natural language query for memory recall
        memories (list): List of memory objects to search through
        
    Returns:
        list: Sorted list of relevant memories
    """
    # If we have no memories, return an empty list
    if not memories:
        return []
    
    # Simple keyword search as fallback method
    def keyword_search(query_text, memory_list):
        query_words = query_text.lower().split()
        
        # Score memories based on word overlap
        scored_memories = []
        for memory in memory_list:
            memory_text = memory.get('text', '').lower()
            memory_emotion = memory.get('emotion', '').lower()
            memory_location = memory.get('location', '').lower()
            memory_people = ' '.join([p.lower() for p in memory.get('people', [])])
            
            # Count matching words
            score = sum(1 for word in query_words if word in memory_text)
            # Bonus for emotion matches
            score += sum(3 for word in query_words if word in memory_emotion)
            # Bonus for location matches
            score += sum(2 for word in query_words if word in memory_location)
            # Bonus for people matches
            score += sum(2 for word in query_words if word in memory_people)
            
            # Store score
            memory_copy = memory.copy()
            memory_copy['relevance_score'] = score
            scored_memories.append(memory_copy)
        
        # Sort by score in descending order
        return sorted(scored_memories, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    try:
        # Generate query embedding for semantic search
        query_embedding = generate_memory_embedding(query)
        
        try:
            # Try to use OpenAI to extract search parameters
            search_params_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at understanding memory recall queries. "
                        "Given a query about someone's memories, extract key search parameters like: "
                        "- Emotions mentioned (happy, sad, etc.) "
                        "- People mentioned "
                        "- Time periods mentioned (last week, childhood, etc.) "
                        "- Locations mentioned "
                        "- Topics or themes mentioned "
                        "Respond with a JSON object containing these parameters."
                    },
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"},
            )
            
            # Parse search parameters
            search_params = json.loads(search_params_response.choices[0].message.content)
            
            # Filter memories based on explicit search parameters
            filtered_memories = memories.copy()
            
            if 'emotions' in search_params and search_params['emotions']:
                filtered_memories = [
                    m for m in filtered_memories 
                    if any(emotion.lower() in m.get('emotion', '').lower() for emotion in search_params['emotions'])
                ]
            
            if 'people' in search_params and search_params['people']:
                filtered_memories = [
                    m for m in filtered_memories 
                    if any(person.lower() in [p.lower() for p in m.get('people', [])] for person in search_params['people'])
                ]
            
            if 'locations' in search_params and search_params['locations']:
                filtered_memories = [
                    m for m in filtered_memories 
                    if any(location.lower() in m.get('location', '').lower() for location in search_params['locations'])
                ]
        except Exception as api_error:
            print(f"API error when extracting search parameters: {api_error}")
            # Fall back to basic filtering
            filtered_memories = memories.copy()
            
            # Extract potential keywords from query
            query_lower = query.lower()
            common_emotions = ['happy', 'sad', 'angry', 'excited', 'frustrated', 'anxious', 'peaceful']
            
            # Simple emotion filtering
            for emotion in common_emotions:
                if emotion in query_lower:
                    filtered_memories = [
                        m for m in filtered_memories 
                        if emotion in m.get('emotion', '').lower()
                    ]
                    break
        
        # If we have embeddings for semantic similarity
        if query_embedding and filtered_memories:
            # Calculate cosine similarity between query and memory embeddings
            for memory in filtered_memories:
                if memory.get('embedding'):
                    # Make sure we're comparing vectors of the same length
                    min_len = min(len(query_embedding), len(memory.get('embedding')))
                    # Simple cosine similarity - dot product of normalized vectors
                    similarity = sum(a*b for a, b in zip(query_embedding[:min_len], memory.get('embedding')[:min_len]))
                    memory['relevance_score'] = similarity
                else:
                    memory['relevance_score'] = 0
            
            # Sort by relevance score
            filtered_memories.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        try:
            # Try to use OpenAI for final ranking
            if filtered_memories:
                memories_json = json.dumps([{
                    'id': m.get('id'),
                    'text': m.get('text'),
                    'date': m.get('date'),
                    'emotion': m.get('emotion'),
                    'people': m.get('people', []),
                    'location': m.get('location')
                } for m in filtered_memories[:20]])  # Limit to 20 for API constraints
                
                final_ranking_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at helping users recall their personal memories. "
                            "Given a query and a set of memories, select and rank the most relevant memories "
                            "that best answer the query. Return a JSON array of memory IDs in order of relevance."
                        },
                        {
                            "role": "user", 
                            "content": f"Query: {query}\n\nMemories: {memories_json}"
                        }
                    ],
                    response_format={"type": "json_object"},
                )
                
                # Get the ranked memory IDs
                final_ranking = json.loads(final_ranking_response.choices[0].message.content)
                ranked_ids = final_ranking.get('memory_ids', [])
                
                # Create a mapping of id to memory
                memory_map = {m.get('id'): m for m in filtered_memories}
                
                # Reorder memories based on final ranking
                ranked_memories = [memory_map[mem_id] for mem_id in ranked_ids if mem_id in memory_map]
                
                # Add any remaining memories that weren't in the ranked list
                remaining_memories = [m for m in filtered_memories if m.get('id') not in ranked_ids]
                
                return ranked_memories + remaining_memories
        except Exception as api_error:
            print(f"API error in final ranking: {api_error}")
            # API failed, just use the filtered memories
        
        return filtered_memories if filtered_memories else keyword_search(query, memories)
    
    except Exception as e:
        print(f"Error recalling memories: {e}")
        # Fall back to simple keyword search
        return keyword_search(query, memories)

def analyze_emotion(text):
    """
    Analyze the emotional content of a memory.
    
    Args:
        text (str): The memory text
        
    Returns:
        str: The dominant emotion detected
    """
    # List of emotions to check for
    emotions = {
        'Happy': ['happy', 'joy', 'delighted', 'pleased', 'cheerful', 'content', 'joy'],
        'Sad': ['sad', 'unhappy', 'depressed', 'down', 'blue', 'upset', 'gloomy'],
        'Angry': ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'frustrated'],
        'Surprised': ['surprised', 'shocked', 'astonished', 'amazed', 'stunned'],
        'Anxious': ['anxious', 'worried', 'nervous', 'stressed', 'uneasy', 'concerned'],
        'Peaceful': ['peaceful', 'calm', 'relaxed', 'tranquil', 'serene', 'content'],
        'Nostalgic': ['nostalgic', 'remember', 'memory', 'past', 'childhood', 'reminisce'],
        'Excited': ['excited', 'thrilled', 'eager', 'enthusiastic', 'energetic'],
        'Grateful': ['grateful', 'thankful', 'appreciate', 'blessed', 'fortunate'],
        'Confused': ['confused', 'puzzled', 'perplexed', 'bewildered', 'uncertain'],
        'Proud': ['proud', 'accomplished', 'achievement', 'satisfied'],
        'Embarrassed': ['embarrassed', 'ashamed', 'humiliated', 'mortified'],
        'Hopeful': ['hopeful', 'optimistic', 'looking forward', 'anticipate'],
        'Neutral': []  # Default if no other emotion is detected
    }
    
    try:
        # Try to use the OpenAI API for advanced emotion analysis
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at detecting emotions in text. "
                    "Given a personal memory, identify the dominant emotion expressed. "
                    "Choose from: Happy, Sad, Angry, Surprised, Anxious, Peaceful, Nostalgic, "
                    "Excited, Grateful, Confused, Proud, Embarrassed, Hopeful, or Neutral. "
                    "Respond with just the emotion name."
                },
                {"role": "user", "content": text}
            ]
        )
        
        emotion = response.choices[0].message.content.strip()
        return emotion
    
    except Exception as e:
        print(f"Error analyzing emotion: {e}")
        
        # Fall back to basic keyword-based analysis
        text_lower = text.lower()
        emotion_scores = {emotion: 0 for emotion in emotions}
        
        # Count emotion keyword occurrences
        for emotion, keywords in emotions.items():
            for keyword in keywords:
                if keyword in text_lower:
                    emotion_scores[emotion] += 1
        
        # If we found emotional content, return the dominant emotion
        if any(emotion_scores.values()):
            return max(emotion_scores.items(), key=lambda x: x[1])[0]
            
        # Default fallback
        return "Neutral"

def summarize_memories(memories, time_period):
    """
    Create an AI-generated summary of memories from a specific time period.
    
    Args:
        memories (list): List of memory objects to summarize
        time_period (str): The time period being summarized (e.g., "Past Week")
        
    Returns:
        str: A summary of the memories
    """
    # Basic summary generator as fallback
    def basic_summary_generator(memory_list, period):
        # Extract key information
        total_memories = len(memory_list)
        if total_memories == 0:
            return "No memories found for this time period."
            
        # Get emotional trends
        emotions = {}
        for memory in memory_list:
            emotion = memory.get('emotion', 'Neutral')
            emotions[emotion] = emotions.get(emotion, 0) + 1
        
        # Find dominant emotion
        dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0] if emotions else "Neutral"
        
        # Extract locations
        locations = {}
        for memory in memory_list:
            loc = memory.get('location', 'Unknown')
            if loc != 'Unknown':
                locations[loc] = locations.get(loc, 0) + 1
        
        # Find common locations
        common_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3]
        location_text = ", ".join([loc for loc, count in common_locations]) if common_locations else "various places"
        
        # Extract people
        people = {}
        for memory in memory_list:
            for person in memory.get('people', []):
                people[person] = people.get(person, 0) + 1
        
        # Find frequently mentioned people
        frequent_people = sorted(people.items(), key=lambda x: x[1], reverse=True)[:3]
        people_text = ", ".join([person for person, count in frequent_people]) if frequent_people else "various people"
        
        # Generate basic summary
        summary = f"""
### Your {period} in Review

During this period, you recorded **{total_memories} memories**. 

**Emotional Trends:** 
You primarily felt **{dominant_emotion}** during this time. {
"Other emotions you experienced include " + ", ".join([e for e in emotions.keys() if e != dominant_emotion][:3]) + "." 
if len(emotions) > 1 else ""
}

**Places & People:** 
Your memories took place in {location_text}. {
"You shared these moments with " + people_text + "." if people_text != "various people" else ""
}

**Reflection:**
This {period.lower()} appears to have been a time of {
"joy and positivity" if dominant_emotion in ["Happy", "Excited", "Grateful", "Peaceful"] 
else "reflection and introspection" if dominant_emotion in ["Nostalgic", "Hopeful"] 
else "challenges and growth" if dominant_emotion in ["Sad", "Angry", "Anxious"] 
else "various experiences"
}. Remember that each memory, whether positive or challenging, contributes to your personal journey.
        """
        
        return summary
    
    try:
        # Convert memories to a simplified format for the API
        memories_text = []
        for memory in memories:
            memory_str = f"Date: {memory.get('date')[:10]}\n"
            memory_str += f"Content: {memory.get('text')}\n"
            memory_str += f"Emotion: {memory.get('emotion')}\n"
            if memory.get('people'):
                memory_str += f"People: {', '.join(memory.get('people'))}\n"
            if memory.get('location') and memory.get('location') != 'Unknown':
                memory_str += f"Location: {memory.get('location')}\n"
            memories_text.append(memory_str)
        
        memories_combined = "\n---\n".join(memories_text)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert at summarizing personal memories and finding insights. "
                    f"Given a collection of personal memories from the {time_period}, create a thoughtful summary that: "
                    f"1. Identifies major themes and patterns "
                    f"2. Notes emotional trends "
                    f"3. Highlights significant events or moments "
                    f"4. Provides gentle insights that might be valuable to the person "
                    f"5. Maintains a warm, supportive tone "
                    f"Write in second person (you/your) as if speaking directly to the memory owner."
                },
                {"role": "user", "content": memories_combined}
            ]
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error summarizing memories: {e}")
        # Use the basic summary generator as fallback
        return basic_summary_generator(memories, time_period)

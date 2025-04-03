import datetime
import random
import string
import re

def get_current_date():
    """
    Get the current date and time in ISO format.
    
    Returns:
        str: Current date and time in ISO format
    """
    return datetime.datetime.now().isoformat()

def parse_date(date_str):
    """
    Parse a date string into a datetime object.
    
    Args:
        date_str (str): Date string in ISO format
        
    Returns:
        datetime.datetime: Parsed datetime object, or None if parsing fails
    """
    try:
        return datetime.datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None

def format_date(date_obj, format_str="%B %d, %Y"):
    """
    Format a datetime object as a string.
    
    Args:
        date_obj (datetime.datetime): Datetime object to format
        format_str (str): Format string
        
    Returns:
        str: Formatted date string
    """
    if isinstance(date_obj, datetime.datetime):
        return date_obj.strftime(format_str)
    elif isinstance(date_obj, str):
        date_obj = parse_date(date_obj)
        if date_obj:
            return date_obj.strftime(format_str)
    return "Unknown date"

def generate_id():
    """
    Generate a random ID string.
    
    Returns:
        str: Random ID string
    """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(10))

def extract_people_from_text(text):
    """
    Simple helper to try to extract names of people from text.
    This is a basic implementation and not as sophisticated as AI-based extraction.
    
    Args:
        text (str): Text to extract names from
        
    Returns:
        list: List of potential names extracted from text
    """
    # This is a very basic implementation
    # A more sophisticated version would use NER (Named Entity Recognition)
    
    # Look for patterns like "with [Name]" or "and [Name]"
    with_pattern = re.compile(r'with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)')
    and_pattern = re.compile(r'and\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)')
    
    people = []
    
    # Extract names from "with [Name]" pattern
    with_matches = with_pattern.findall(text)
    people.extend(with_matches)
    
    # Extract names from "and [Name]" pattern
    and_matches = and_pattern.findall(text)
    people.extend(and_matches)
    
    # Remove duplicates and return
    return list(set(people))

def extract_location_from_text(text):
    """
    Simple helper to try to extract locations from text.
    This is a basic implementation and not as sophisticated as AI-based extraction.
    
    Args:
        text (str): Text to extract locations from
        
    Returns:
        str: Potential location extracted from text, or None if no location found
    """
    # This is a very basic implementation
    # A more sophisticated version would use NER (Named Entity Recognition)
    
    # Look for patterns like "at [Location]" or "in [Location]"
    at_pattern = re.compile(r'at\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)')
    in_pattern = re.compile(r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)')
    
    # Extract location from "at [Location]" pattern
    at_matches = at_pattern.findall(text)
    if at_matches:
        return at_matches[0]
    
    # Extract location from "in [Location]" pattern
    in_matches = in_pattern.findall(text)
    if in_matches:
        return in_matches[0]
    
    return None

def truncate_text(text, max_length=100):
    """
    Truncate text to a maximum length and add ellipsis if needed.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length before truncation
        
    Returns:
        str: Truncated text
    """
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

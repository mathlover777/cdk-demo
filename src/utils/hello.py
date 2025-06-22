"""
Shared hello utility functions that can be used across different services
(API, Lambda, Fargate, etc.)
"""

def get_hello_message(service_name: str = "Backend") -> dict:
    """
    Generate a hello message that can be used by any service
    
    Args:
        service_name: Name of the service calling this function
        
    Returns:
        dict: Hello message with service name
    """
    return {
        "message": f"Hello from {service_name}!",
        "service": service_name,
        "timestamp": "2024-01-01T00:00:00Z"  # In real app, use datetime.now()
    }

def get_hello_message_with_user(user_name: str, service_name: str = "Backend") -> dict:
    """
    Generate a personalized hello message
    
    Args:
        user_name: Name of the user
        service_name: Name of the service calling this function
        
    Returns:
        dict: Personalized hello message
    """
    return {
        "message": f"Hello {user_name} from {service_name}!",
        "user": user_name,
        "service": service_name,
        "timestamp": "2024-01-01T00:00:00Z"
    } 
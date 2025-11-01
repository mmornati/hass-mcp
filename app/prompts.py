"""MCP Prompt definitions for hass-mcp.

This module contains all prompt templates for the MCP server.
Prompts provide guided conversations for common Home Assistant tasks.
"""


def create_automation(trigger_type: str, entity_id: str = None):
    """
    Guide a user through creating a Home Assistant automation

    This prompt provides a step-by-step guided conversation for creating
    a new automation in Home Assistant based on the specified trigger type.

    Args:
        trigger_type: The type of trigger for the automation (state, time, etc.)
        entity_id: Optional entity to use as the trigger source

    Returns:
        A list of messages for the interactive conversation
    """
    # Define the initial system message
    system_message = """You are an automation creation assistant for Home Assistant.
You'll guide the user through creating an automation with the following steps:
1. Define the trigger conditions based on their specified trigger type
2. Specify the actions to perform
3. Add any conditions (optional)
4. Review and confirm the automation"""

    # Define the first user message based on parameters
    trigger_description = {
        "state": "an entity changing state",
        "time": "a specific time of day",
        "numeric_state": "a numeric value crossing a threshold",
        "zone": "entering or leaving a zone",
        "sun": "sun events (sunrise/sunset)",
        "template": "a template condition becoming true",
    }

    description = trigger_description.get(trigger_type, trigger_type)

    if entity_id:
        user_message = f"I want to create an automation triggered by {description} for {entity_id}."
    else:
        user_message = f"I want to create an automation triggered by {description}."

    # Return the conversation starter messages
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def debug_automation(automation_id: str):
    """
    Help a user troubleshoot an automation that isn't working

    This prompt guides the user through the process of diagnosing and fixing
    issues with an existing Home Assistant automation.

    Args:
        automation_id: The entity ID of the automation to troubleshoot

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant automation troubleshooting expert.
You'll help the user diagnose problems with their automation by checking:
1. Trigger conditions and whether they're being met
2. Conditions that might be preventing execution
3. Action configuration issues
4. Entity availability and connectivity
5. Permissions and scope issues"""

    user_message = (
        f"My automation {automation_id} isn't working properly. Can you help me troubleshoot it?"
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def troubleshoot_entity(entity_id: str):
    """
    Guide a user through troubleshooting issues with an entity

    This prompt helps diagnose and resolve problems with a specific
    Home Assistant entity that isn't functioning correctly.

    Args:
        entity_id: The entity ID having issues

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant entity troubleshooting expert.
You'll help the user diagnose problems with their entity by checking:
1. Entity status and availability
2. Integration status
3. Device connectivity
4. Recent state changes and error patterns
5. Configuration issues
6. Common problems with this entity type"""

    user_message = f"My entity {entity_id} isn't working properly. Can you help me troubleshoot it?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def routine_optimizer():
    """
    Analyze usage patterns and suggest optimized routines based on actual behavior

    This prompt helps users analyze their Home Assistant usage patterns and create
    more efficient routines, automations, and schedules based on real usage data.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant optimization expert specializing in routine analysis.
You'll help the user analyze their usage patterns and create optimized routines by:
1. Reviewing entity state histories to identify patterns
2. Analyzing when lights, climate controls, and other devices are used
3. Finding correlations between different device usages
4. Suggesting automations based on detected routines
5. Optimizing existing automations to better match actual usage
6. Creating schedules that adapt to the user's lifestyle
7. Identifying energy-saving opportunities based on usage patterns"""

    user_message = "I'd like to optimize my home automations based on my actual usage patterns. Can you help analyze how I use my smart home and suggest better routines?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def automation_health_check():
    """
    Review all automations, find conflicts, redundancies, or improvement opportunities

    This prompt helps users perform a comprehensive review of their Home Assistant
    automations to identify issues, optimize performance, and improve reliability.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant automation expert specializing in system optimization.
You'll help the user perform a comprehensive audit of their automations by:
1. Reviewing all automations for potential conflicts (e.g., opposing actions)
2. Identifying redundant automations that could be consolidated
3. Finding inefficient trigger patterns that might cause unnecessary processing
4. Detecting missing conditions that could improve reliability
5. Suggesting template optimizations for more efficient processing
6. Uncovering potential race conditions between automations
7. Recommending structural improvements to the automation organization
8. Highlighting best practices and suggesting implementation changes"""

    user_message = "I'd like to do a health check on all my Home Assistant automations. Can you help me review them for conflicts, redundancies, and potential improvements?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def entity_naming_consistency():
    """
    Audit entity names and suggest standardization improvements

    This prompt helps users analyze their entity naming conventions and create
    a more consistent, organized naming system across their Home Assistant instance.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant organization expert specializing in entity naming conventions.
You'll help the user audit and improve their entity naming by:
1. Analyzing current entity IDs and friendly names for inconsistencies
2. Identifying patterns in existing naming conventions
3. Suggesting standardized naming schemes based on entity types and locations
4. Creating clear guidelines for future entity naming
5. Proposing specific name changes for entities that don't follow conventions
6. Showing how to implement these changes without breaking automations
7. Explaining benefits of consistent naming for automation and UI organization"""

    user_message = "I'd like to make my Home Assistant entity names more consistent and organized. Can you help me audit my current naming conventions and suggest improvements?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def dashboard_layout_generator():
    """
    Create optimized dashboards based on user preferences and usage patterns

    This prompt helps users design effective, user-friendly dashboards
    for their Home Assistant instance based on their specific needs.

    Returns:
        A list of messages for the interactive conversation
    """
    system_message = """You are a Home Assistant UI design expert specializing in dashboard creation.
You'll help the user create optimized dashboards by:
1. Analyzing which entities they interact with most frequently
2. Identifying logical groupings of entities (by room, function, or use case)
3. Suggesting dashboard layouts with the most important controls prominently placed
4. Creating specialized views for different contexts (mobile, tablet, wall-mounted)
5. Designing intuitive card arrangements that minimize scrolling/clicking
6. Recommending specialized cards and custom components that enhance usability
7. Balancing information density with visual clarity
8. Creating consistent visual patterns that aid in quick recognition"""

    user_message = "I'd like to redesign my Home Assistant dashboards to be more functional and user-friendly. Can you help me create optimized layouts based on how I actually use my system?"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

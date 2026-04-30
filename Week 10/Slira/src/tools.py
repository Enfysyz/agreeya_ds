import os
import logging
from jira import JIRA

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
# -----------------------------

jira_options = {'server': os.environ.get('JIRA_SERVER_URL')}
jira_client = JIRA(
    options=jira_options, 
    basic_auth=(os.environ.get('JIRA_EMAIL'), os.environ.get('JIRA_API_TOKEN'))
)

def create_jira_ticket(summary: str, description: str, project_key: str, action: str, issue_type: str = "Task", due_date: str = None) -> str:
    """Handles Jira ticket creation and drafting.
    
    Args:
        summary: The title or short name of the ticket.
        description: The detailed explanation of the ticket.
        project_key: The short, uppercase prefix of the project (e.g., KAN, DEV, PROJ).
        action: MUST be exactly 'DRAFT' when first asked. ONLY use 'CREATE' if the user has explicitly replied 'yes' or approved the draft.
        issue_type: The type of ticket (defaults to 'Task').
        due_date: (Optional) The deadline formatted exactly as YYYY-MM-DD.
    """
    logger.info(f"[create_jira_ticket] INPUT: project='{project_key}', action='{action}', due='{due_date}'")
    
    if action.upper() != "CREATE":
        logger.info("[create_jira_ticket] Action was DRAFT. Blocking Jira API call.")
        draft_msg = f"Here is the draft for your ticket:\n*Project:* {project_key}\n*Summary:* {summary}\n*Description:* {description}\n*Due Date:* {due_date or 'N/A'}\n\nShould I go ahead and create this ticket?"
        return draft_msg
        
    try:
        issue_fields = {
            'project': project_key,
            'summary': summary,
            'description': description,
            'issuetype': {'name': issue_type}
        }
        
        if due_date:
            issue_fields['duedate'] = due_date
            
        new_issue = jira_client.create_issue(**issue_fields)
        result = f"Successfully created ticket: {new_issue.key}"
        logger.info(f"[create_jira_ticket] RESULT: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to create ticket: {str(e)}"
        logger.error(f"[create_jira_ticket] ERROR: {error_msg}")
        return error_msg

def move_jira_ticket(issue_key: str, transition_name: str) -> str:
    """Moves or transitions a Jira ticket to a new status.
    
    Args:
        issue_key: The full ticket ID (e.g., KAN-123).
        transition_name: The name of the status to move it to (e.g., 'In Progress', 'Done').
    """
    logger.info(f"[move_jira_ticket] INPUT: issue_key='{issue_key}', transition_name='{transition_name}'")
    
    try:
        issue = jira_client.issue(issue_key)
        transitions = jira_client.transitions(issue)
        
        transition_id = None
        for t in transitions:
            if t['name'].lower() == transition_name.lower():
                transition_id = t['id']
                break
                
        if not transition_id:
            result = f"Transition '{transition_name}' not found for {issue_key}."
            logger.info(f"[move_jira_ticket] RESULT: {result}")
            return result
            
        jira_client.transition_issue(issue, transition_id)
        result = f"Successfully moved {issue_key} to {transition_name}."
        logger.info(f"[move_jira_ticket] RESULT: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to move ticket: {str(e)}"
        logger.error(f"[move_jira_ticket] ERROR: {error_msg}")
        return error_msg
    
def get_my_tasks(timeframe: str = "all") -> str:
    """Fetches Jira tasks assigned to the user based on a timeframe.
    
    Args:
        timeframe: Must be 'today', 'overdue', or 'all'.
    """
    logger.info(f"[get_my_tasks] INPUT: timeframe='{timeframe}'")
    
    jql = "assignee = currentUser() AND resolution is EMPTY"
    
    if timeframe.lower() == 'today':
        jql += " AND due >= startOfDay() AND due <= endOfDay()"
    elif timeframe.lower() == 'overdue':
        jql += " AND due < startOfDay()"
        
    try:
        issues = jira_client.search_issues(jql, maxResults=10)
        logger.info(f"[get_my_tasks] ACTION: Jira returned {len(issues)} issues.")
        
        if not issues:
            result = f"Great news! You have no {timeframe} tasks."
            logger.info(f"[get_my_tasks] RESULT: {result}")
            return result
            
        result = f"*Here are your {timeframe} tasks:*\n\n"
        
        for issue in issues:
            due_date = issue.fields.duedate or "No Due Date"
            result += f"- [{issue.key}] {issue.fields.summary} (Due: {due_date})\n"
            
        logger.info(f"[get_my_tasks] RESULT: {result.replace(chr(10), ' | ')}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to get tasks: {str(e)}"
        logger.error(f"[get_my_tasks] ERROR: {error_msg}")
        return error_msg

def get_daily_summary() -> str:
    """Generates a detailed audit log of the user's personal Jira activity from the last 24 hours.
    Use this when the user asks for their daily summary, status report, or 'what did I do today?'.
    """
    logger.info("[get_daily_summary] INPUT: No arguments required.")
    
    # Query: Everything UPDATED by the current user in the last 24 hours
    jql = 'assignee = currentUser() AND updated >= -24h ORDER BY updated DESC'
    
    try:
        # expand='changelog' to see exactly what fields were changed
        issues = jira_client.search_issues(jql, expand='changelog', maxResults=15)
        logger.info(f"[get_daily_summary] ACTION: Jira returned {len(issues)} recently updated issues.")
        
        result = "*📝 Your Personal Activity (Last 24 Hours):*\n\n"
        
        if not issues:
            result += "You haven't modified or updated any tickets in the last 24 hours.\n"
            logger.info(f"[get_daily_summary] RESULT: {result.replace(chr(10), ' | ')}")
            return result
            
        for issue in issues:
            # Default action if no specific changelog event is found
            recent_action = "Updated ticket details or added a comment"
            
            # Identify the specific change made by the user
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories') and issue.changelog.histories:
                latest_history = issue.changelog.histories[-1]
                for item in latest_history.items:
                    if item.field == 'status':
                        recent_action = f"You moved this to '{item.toString}'"
                    elif item.field == 'assignee':
                        recent_action = f"You assigned this to {item.toString}"
                    elif item.field == 'priority':
                        recent_action = f"You changed priority to '{item.toString}'"
            
            result += f"- [{issue.key}] {issue.fields.summary}\n  ↳ *Your Action:* {recent_action}\n"
                
        logger.info(f"[get_daily_summary] RESULT: {result.replace(chr(10), ' | ')}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to get daily summary: {str(e)}"
        logger.error(f"[get_daily_summary] ERROR: {error_msg}")
        return error_msg
    
def get_team_activity(project_key: str = None) -> str:
    """Generates a summary of all Jira activity (updates, creations, status changes) from the last 24 hours.
    If project_key is provided, it filters by that project.
    Use this when the user asks about recent activity, what happened today, or an activity stream.
    """
    logger.info(f"[get_team_activity] INPUT: project_key='{project_key}'")
    
    # Query: Find everything updated in the last 24 hours, sorted by most recent first
    jql = 'updated >= -24h ORDER BY updated DESC'
    if project_key:
        jql = f'project = {project_key} AND updated >= -24h ORDER BY updated DESC'
        
    try:
        issues = jira_client.search_issues(jql, expand='changelog', maxResults=15)
        logger.info(f"[get_team_activity] ACTION: Jira returned {len(issues)} recently updated team issues.")
        
        result = f"*⏱️ Recent Jira Activity (Last 24 Hours){' for ' + project_key if project_key else ''}:*\n\n"
        
        if not issues:
            result += "No tickets were updated or modified in the last 24 hours.\n"
            logger.info(f"[get_team_activity] RESULT: {result.replace(chr(10), ' | ')}")
            return result
            
        for issue in issues:
            recent_action = "Updated or Commented"
            
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories') and issue.changelog.histories:
                latest_history = issue.changelog.histories[-1] 
                author = latest_history.author.displayName if hasattr(latest_history, 'author') else "Someone"
                
                for item in latest_history.items:
                    if item.field == 'status':
                        recent_action = f"Moved to '{item.toString}' by {author}"
                    elif item.field == 'assignee':
                        recent_action = f"Assigned to {item.toString} by {author}"
                    elif item.field == 'description' or item.field == 'summary':
                        recent_action = f"Ticket details edited by {author}"
            
            result += f"- [{issue.key}] {issue.fields.summary}\n  ↳ *Activity:* {recent_action}\n"
                
        logger.info(f"[get_team_activity] RESULT: {result.replace(chr(10), ' | ')}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to get team activity: {str(e)}"
        logger.error(f"[get_team_activity] ERROR: {error_msg}")
        return error_msg
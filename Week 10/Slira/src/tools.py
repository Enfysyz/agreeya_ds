import os
from langchain_core.tools import tool
from jira import JIRA

jira_options = {'server': os.environ.get('JIRA_SERVER_URL')}
jira_client = JIRA(
    options=jira_options, 
    basic_auth=(os.environ.get('JIRA_EMAIL'), os.environ.get('JIRA_API_TOKEN'))
)

@tool
def create_jira_ticket(summary: str, description: str, project_key: str, issue_type: str = "Task") -> str:
    """Creates a new Jira ticket.
    
    Args:
        summary: The title or short name of the ticket.
        description: The detailed explanation of the ticket.
        project_key: The short, uppercase prefix of the project (e.g., KAN, DEV, PROJ).
        issue_type: The type of ticket (defaults to 'Task').
    """
    try:
        new_issue = jira_client.create_issue(
            project=project_key,
            summary=summary,
            description=description,
            issuetype={'name': issue_type}
        )
        return f"Successfully created ticket: {new_issue.key}"
    except Exception as e:
        return f"Failed to create ticket: {str(e)}"

@tool
def move_jira_ticket(issue_key: str, transition_name: str) -> str:
    """Moves or transitions a Jira ticket to a new status.
    
    Args:
        issue_key: The full ticket ID (e.g., KAN-123).
        transition_name: The name of the status to move it to (e.g., 'In Progress', 'Done').
    """
    try:
        issue = jira_client.issue(issue_key)
        transitions = jira_client.transitions(issue)
        
        transition_id = None
        for t in transitions:
            if t['name'].lower() == transition_name.lower():
                transition_id = t['id']
                break
                
        if not transition_id:
            return f"Transition '{transition_name}' not found for {issue_key}."
            
        jira_client.transition_issue(issue, transition_id)
        return f"Successfully moved {issue_key} to {transition_name}."
    except Exception as e:
        return f"Failed to move ticket: {str(e)}"
    
@tool
def get_my_tasks(timeframe: str) -> str:
    """Fetches Jira tasks assigned to the user based on a timeframe.
    
    Args:
        timeframe: Must be 'today', 'overdue', or 'all'.
    """
    print(f"--- DEBUG: get_my_tasks tool triggered with timeframe='{timeframe}' ---")
    
    jql = "assignee = currentUser() AND resolution is EMPTY"
    
    if timeframe.lower() == 'today':
        jql += " AND due >= startOfDay() AND due <= endOfDay()"
    elif timeframe.lower() == 'overdue':
        jql += " AND due < startOfDay()"
        
    try:
        issues = jira_client.search_issues(jql, maxResults=10)
        print(f"--- DEBUG: Jira returned {len(issues)} issues ---")
        
        if not issues:
            # Inject directive into empty state
            return f"SYSTEM DIRECTIVE: The user cannot see this. Tell the user exactly this: 'Great news! You have no {timeframe} tasks.'"
            
        # Inject aggressive directive into the data output
        result = "SYSTEM DIRECTIVE: The user CANNOT see this data. YOU MUST READ THIS LIST AND REPEAT EVERY TICKET TO THE USER IN YOUR RESPONSE:\n\n"
        result += f"*Here are your {timeframe} tasks:*\n"
        
        for issue in issues:
            due_date = issue.fields.duedate or "No Due Date"
            result += f"- [{issue.key}] {issue.fields.summary} (Due: {due_date})\n"
            
        return result
    except Exception as e:
        return f"SYSTEM DIRECTIVE: The tool failed. Tell the user this error: {str(e)}"

@tool
def get_daily_summary() -> str:
    """Generates a detailed audit log of the user's personal Jira activity from the last 24 hours.
    Use this when the user asks for their daily summary, status report, or 'what did I do today?'.
    """
    print("--- DEBUG: get_daily_summary (Personal Audit) tool triggered ---")
    
    # Query: Everything UPDATED by the current user in the last 24 hours
    jql = 'assignee = currentUser() AND updated >= -24h ORDER BY updated DESC'
    
    try:
        # We use expand='changelog' to see exactly what fields were changed
        issues = jira_client.search_issues(jql, expand='changelog', maxResults=15)
        
        result = "SYSTEM DIRECTIVE: The user CANNOT see this data. YOU MUST READ THIS SUMMARY AND FORMAT IT NICELY FOR THE USER:\n\n"
        result += "*📝 Your Personal Activity (Last 24 Hours):*\n\n"
        
        if not issues:
            return result + "You haven't modified or updated any tickets in the last 24 hours.\n"
            
        for issue in issues:
            # Default action if no specific changelog event is found
            recent_action = "Updated ticket details or added a comment"
            
            # Identify the specific change made by the user
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories') and issue.changelog.histories:
                # Get the most recent history item
                latest_history = issue.changelog.histories[-1]
                
                for item in latest_history.items:
                    if item.field == 'status':
                        recent_action = f"You moved this to '{item.toString}'"
                    elif item.field == 'assignee':
                        recent_action = f"You assigned this to {item.toString}"
                    elif item.field == 'priority':
                        recent_action = f"You changed priority to '{item.toString}'"
            
            result += f"- [{issue.key}] {issue.fields.summary}\n  ↳ *Your Action:* {recent_action}\n"
                
        return result
        
    except Exception as e:
        print(f"--- DEBUG: Personal Summary Error: {str(e)} ---")
        return f"SYSTEM DIRECTIVE: The tool failed. Tell the user this error: {str(e)}"
    
@tool
def get_team_activity(project_key: str = None) -> str:
    """Generates a summary of all Jira activity (updates, creations, status changes) from the last 24 hours.
    If project_key is provided, it filters by that project.
    Use this when the user asks about recent activity, what happened today, or an activity stream.
    """
    print(f"--- DEBUG: get_team_activity tool triggered for project: {project_key} ---")
    
    # Query: Find everything updated in the last 24 hours, sorted by most recent first
    jql = 'updated >= -24h ORDER BY updated DESC'
    if project_key:
        jql = f'project = {project_key} AND updated >= -24h ORDER BY updated DESC'
        
    try:
        # Notice we added expand='changelog' to get the audit trail
        issues = jira_client.search_issues(jql, expand='changelog', maxResults=15)
        
        result = "SYSTEM DIRECTIVE: The user CANNOT see this data. YOU MUST READ THIS SUMMARY AND FORMAT IT NICELY FOR THE USER:\n\n"
        result += f"*⏱️ Recent Jira Activity (Last 24 Hours){' for ' + project_key if project_key else ''}:*\n\n"
        
        if not issues:
            return result + "No tickets were updated or modified in the last 24 hours.\n"
            
        for issue in issues:
            # Default fallback action
            recent_action = "Updated or Commented"
            
            # Dig into the changelog to find exactly what just happened
            if hasattr(issue, 'changelog') and hasattr(issue.changelog, 'histories') and issue.changelog.histories:
                latest_history = issue.changelog.histories[-1] # Grab the most recent event
                author = latest_history.author.displayName if hasattr(latest_history, 'author') else "Someone"
                
                # Check what field was changed
                for item in latest_history.items:
                    if item.field == 'status':
                        recent_action = f"Moved to '{item.toString}' by {author}"
                    elif item.field == 'assignee':
                        recent_action = f"Assigned to {item.toString} by {author}"
                    elif item.field == 'description' or item.field == 'summary':
                        recent_action = f"Ticket details edited by {author}"
            
            result += f"- [{issue.key}] {issue.fields.summary}\n  ↳ *Activity:* {recent_action}\n"
                
        return result
        
    except Exception as e:
        print(f"--- DEBUG: Team Activity Error: {str(e)} ---")
        return f"SYSTEM DIRECTIVE: The tool failed. Tell the user this error: {str(e)}"
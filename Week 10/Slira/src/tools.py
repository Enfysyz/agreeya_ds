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
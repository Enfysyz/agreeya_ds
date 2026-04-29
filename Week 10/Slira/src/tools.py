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
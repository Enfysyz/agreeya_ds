import os
from langchain_core.tools import tool
from jira import JIRA

# Initialize Jira client
jira_options = {'server': os.environ.get('JIRA_SERVER_URL')}
jira_client = JIRA(
    options=jira_options, 
    basic_auth=(os.environ.get('JIRA_EMAIL'), os.environ.get('JIRA_API_TOKEN'))
)

@tool
def create_jira_ticket(summary: str, description: str, project_key: str, issue_type: str = "Task") -> str:
    """Creates a new Jira ticket. Use this when the user asks to open, create, or make a ticket."""
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
    """Moves or transitions a Jira ticket (e.g., to 'In Progress' or 'Done')."""
    try:
        issue = jira_client.issue(issue_key)
        transitions = jira_client.transitions(issue)
        
        # Find the ID for the requested transition state
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
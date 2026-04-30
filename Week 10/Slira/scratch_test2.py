import os
import sys

# Ensure src module can be imported
sys.path.append(r'c:\MySpace\USC\Sem 4\AgreeYa\agreeya_ds\Week 10\Slira')

from src.agent import llm, RouterOutput, system_prompt
from langchain_core.messages import SystemMessage, HumanMessage

full_prompt = """--- SYSTEM CALENDAR ---
Today: Thursday, 2026-04-30
Tomorrow: Friday, 2026-05-01
In 2 days: Saturday, 2026-05-02
In 3 days: Sunday, 2026-05-03

--- PREVIOUS THREAD CONTEXT ---

--- USER COMMAND ---
Create a ticket in the KAN project. The summary should be 'Fix login page typo' and the description is 'The login button says logun, please fix it'."""

prompt = [
    SystemMessage(content=system_prompt), 
    HumanMessage(content=full_prompt)
]

structured_llm = llm.with_structured_output(RouterOutput)

try:
    response = structured_llm.invoke(prompt)
    print('SUCCESS:')
    print(response.model_dump())
except Exception as e:
    print('ERROR:')
    print(e)

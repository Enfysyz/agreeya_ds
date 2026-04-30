import os
import sys
import uuid
import asyncio

sys.path.append(r'c:\MySpace\USC\Sem 4\AgreeYa\agreeya_ds\Week 10\Slira')
from src.agent import graph
from langchain_core.messages import HumanMessage, AIMessage

async def test():
    config = {"configurable": {"thread_id": "test_thread"}}
    
    print("USER: Create a ticket in the KAN project. The summary should be 'Fix login page typo' and the description is 'The login button says logun, please fix it'.")
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content="Create a ticket in the KAN project. The summary should be 'Fix login page typo' and the description is 'The login button says logun, please fix it'.")]},
        config
    )
    print("BOT:", result["messages"][-1].content)
    
    print("USER: yup")
    result2 = await graph.ainvoke(
        {"messages": [HumanMessage(content="yup")]},
        config
    )
    print("BOT:", result2["messages"][-1].content)

asyncio.run(test())

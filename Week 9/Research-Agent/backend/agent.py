import os
import asyncio
from typing import List
from bs4 import BeautifulSoup
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ddgs import DDGS
from playwright.async_api import async_playwright

class ResearchAgent:
    def __init__(self, websocket):
        self.websocket = websocket
        # Connect to the Ollama container. For 8GB VRAM, 'mistral' or 'llama3' (8B) are ideal.
        # Note: You must pull the model manually once via: docker exec -it <ollama_container_id> ollama pull mistral
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = Ollama(base_url=ollama_url, model="llama3")

    async def log(self, message: str, url: str = None):
        """Sends real-time updates to the frontend."""
        payload = {"type": "log", "message": message}
        if url:
            payload["url"] = url
        await self.websocket.send_json(payload)

    async def search_web(self, query: str, max_results: int = 3) -> List[dict]:
        """Uses DuckDuckGo to find relevant URLs."""
        await self.log(f"Searching the web for: '{query}'")
        
        # We wrap the synchronous DDGS call in a dedicated function
        # and run it in a thread so it doesn't block your async event loop.
        def perform_search():
            results = []
            with DDGS() as ddgs:
                # DuckDuckGo occasionally rate-limits or throws minor errors, 
                # so a try/except block is good practice here.
                try:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(r)
                except Exception as e:
                    print(f"DuckDuckGo search error: {e}")
            return results

        # Execute the synchronous search in a background thread
        results = await asyncio.to_thread(perform_search)
        return results

    async def scrape_url(self, url: str) -> str:
        """Navigates to the URL and extracts text using headless Chromium."""
        await self.log(f"Navigating and extracting content...", url=url)
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                # Wait until there are no network connections for at least 500 ms.
                await page.goto(url, wait_until="networkidle", timeout=15000)
                html = await page.content()
                await browser.close()

                # Clean up HTML to plain text
                soup = BeautifulSoup(html, "html.parser")
                for script in soup(["script", "style", "nav", "footer"]):
                    script.extract()
                text = soup.get_text(separator=' ', strip=True)
                
                # Truncate to avoid blowing up the LLM context window (roughly 4000 words max for safety)
                return text[:15000] 
        except Exception as e:
            await self.log(f"Failed to scrape {url}: {str(e)}", url=url)
            return ""

    async def summarize_content(self, topic: str, content: str, url: str) -> str:
        """Uses Ollama to extract relevant information."""
        await self.log(f"Analyzing content with local LLM...", url=url)
        prompt = PromptTemplate(
            input_variables=["topic", "content"],
            template="You are a research assistant. Extract the most important facts about '{topic}' from the following text. If there is no relevant information, reply with 'No relevant information found.'\n\nText:\n{content}\n\nSummary:"
        )
        # Run LLM synchronously in an executor to not block the async event loop
        chain = prompt | self.llm
        result = await asyncio.to_thread(chain.invoke, {"topic": topic, "content": content})
        return result

    async def run_research(self, topic: str):
        """The main deep-research execution loop."""
        await self.log("Initializing Deep Research protocol...")
        
        search_results = await self.search_web(topic, max_results=3)
        
        if not search_results:
            await self.websocket.send_json({"type": "complete", "result": "No results found on the web."})
            return

        aggregated_findings = []

        for result in search_results:
            url = result['href']
            snippet = result['body']
            await self.log(f"Found source: {result['title']}", url=url)
            
            # Scrape and summarize
            page_text = await self.scrape_url(url)
            if page_text:
                summary = await self.summarize_content(topic, page_text, url)
                if "No relevant information found" not in summary:
                    aggregated_findings.append(f"Source: {url}\nFindings: {summary}")

        await self.log("Synthesizing final report...")
        
        if not aggregated_findings:
             await self.websocket.send_json({"type": "complete", "result": "Visited several sites but found no concrete information."})
             return

        # Final Synthesis
        final_prompt = f"Write a comprehensive final report on '{topic}' based ONLY on the following findings:\n\n" + "\n\n".join(aggregated_findings)
        final_report = await asyncio.to_thread(self.llm.invoke, final_prompt)

        await self.websocket.send_json({
            "type": "complete",
            "result": final_report
        })
import os
import json
import asyncio
from typing import List, AsyncGenerator
from bs4 import BeautifulSoup
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from ddgs import DDGS
from playwright.async_api import async_playwright

class ResearchAgent:
    def __init__(self):
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llm = Ollama(base_url=ollama_url, model="llama3")

    def _format_sse(self, data: dict) -> str:
        """Formats standard Python dictionaries into SSE-compliant strings."""
        return f"data: {json.dumps(data)}\n\n"

    async def search_web(self, query: str, max_results: int = 3) -> List[dict]:
        """Uses DuckDuckGo to find relevant URLs."""
        def perform_search():
            results = []
            with DDGS() as ddgs:
                try:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(r)
                except Exception as e:
                    print(f"DuckDuckGo search error: {e}")
            return results

        return await asyncio.to_thread(perform_search)

    async def scrape_url(self, url: str) -> str:
        """Navigates to the URL and extracts text using headless Chromium."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=15000)
                html = await page.content()
                await browser.close()

                soup = BeautifulSoup(html, "html.parser")
                for script in soup(["script", "style", "nav", "footer"]):
                    script.extract()
                text = soup.get_text(separator=' ', strip=True)
                
                return text[:15000] 
        except Exception as e:
            return ""

    async def summarize_content(self, topic: str, content: str) -> str:
        """Uses Ollama to extract relevant information."""
        prompt = PromptTemplate(
            input_variables=["topic", "content"],
            template="You are a research assistant. Extract the most important facts about '{topic}' from the following text. If there is no relevant information, reply with 'No relevant information found.'\n\nText:\n{content}\n\nSummary:"
        )
        chain = prompt | self.llm
        result = await asyncio.to_thread(chain.invoke, {"topic": topic, "content": content})
        return result

    async def run_research(self, topic: str) -> AsyncGenerator[str, None]:
        """The main deep-research execution loop yielding SSE strings."""
        
        # Notice we use 'yield' instead of sending via websocket
        yield self._format_sse({"type": "log", "message": "Initializing Deep Research protocol..."})
        
        search_results = await self.search_web(topic, max_results=3)
        
        if not search_results:
            yield self._format_sse({"type": "complete", "result": "No results found on the web."})
            return

        aggregated_findings = []

        for result in search_results:
            url = result['href']
            yield self._format_sse({"type": "log", "message": f"Found source: {result['title']}", "url": url})
            yield self._format_sse({"type": "log", "message": "Navigating and extracting content...", "url": url})
            
            page_text = await self.scrape_url(url)
            
            print(f"\n[BACKEND DEBUG] Scraped {url}")
            print(f"[BACKEND DEBUG] Text snippet: {page_text[:300]}...\n")
            
            if page_text:
                yield self._format_sse({"type": "log", "message": "Analyzing content with local LLM...", "url": url})
                summary = await self.summarize_content(topic, page_text)
                
                
                print(f"[BACKEND DEBUG] LLama3 Summary for {url}:")
                print(summary)
                print("-" * 40)
                
                yield self._format_sse({"type": "source_summary", "url": url, "summary": summary, "scraped_text": page_text})
                
                if "No relevant information found" not in summary:
                    aggregated_findings.append(f"Source: {url}\nFindings: {summary}")

        yield self._format_sse({"type": "log", "message": "Synthesizing final report..."})
        
        if not aggregated_findings:
             yield self._format_sse({"type": "complete", "result": "Visited several sites but found no concrete information."})
             return

        # Use a proper LangChain PromptTemplate for the final synthesis
        final_template = PromptTemplate(
            input_variables=["topic", "findings"],
            template="You are an expert research analyst. Write a comprehensive final report on '{topic}' based ONLY on the following findings:\n\n{findings}\n\nFinal Report:"
        )
        
        combined_findings = "\n\n".join(aggregated_findings)
        
        # Add a safety print to your backend terminal so we can see if it's passing data correctly
        print(f"\n--- SENDING TO OLLAMA ---\n{combined_findings[:500]}...\n-------------------------\n")
        
        try:
            chain = final_template | self.llm
            final_report = await asyncio.to_thread(chain.invoke, {"topic": topic, "findings": combined_findings})
            
            # Fallback if the LLM still returns empty
            if not final_report or not final_report.strip():
                final_report = "Error: The local LLM returned an empty response. It may have run out of memory."
                
        except Exception as e:
            final_report = f"Error during final synthesis: {str(e)}"

        yield self._format_sse({"type": "complete", "result": final_report})
from memory.research_mem import ResearchMemory
from tools.host_tracker import host_tracker 
from config.log import logger
from typing import Dict, List
from datetime import datetime
from urllib.parse import urlparse
import requests 
import time
import json
import re
from Model.invokemodel import invoke_model
from extras.safejsonload import safe_json_loads
from config.settings import BRAVE_API_KEY
from tools.extract_urls import extract_urls_from_search_results
from tools.fetch_webpage import fetch_webpage_content

class WebAgent:
    def __init__(self, retriever, llm, prompt, brave_search, wikipedia, provider):
        self.retriever = retriever
        self.llm = llm
        self.prompt = prompt
        self.brave_search = brave_search
        self.wikipedia = wikipedia
        self.provider = provider
        self.max_retries = 3
        self.retry_delay = 2
        self.research_memory = {}
        self.confidence_threshold = 0.5
        self.host_tracker = host_tracker 
        self.current_topic = None
        self.memory = ResearchMemory()
        self.current_assessment = None

    def assess_content_relevance(self, content: str, topic: str) -> Dict:
        assessment_prompt = f"""You are a content assessment expert. Analyze this content's relevance and completeness for the given topic.
        Consider:
        1. How directly it answers the topic/question
        2. The specificity and accuracy of information
        3. Whether it provides context and supporting details
        4. The currentness and reliability of the information
        
        Topic: {topic}
        Content length: {len(content)} characters
        First 1000 chars: {content[:1000]}
        
        You must respond with ONLY a JSON object in this exact format:
        {{
            "relevance": <number between 0-1>,
            "is_complete": <true or false>,
            "found_data": "<key information found>",
            "needs_verification": <true or false>,
            "needs_context": <true or false>,
            "confidence": <number between 0-1>
        }}"""
        
        try:
            response = invoke_model(self.llm, assessment_prompt)
            response_text = response.content.strip()
            json_match = re.search(r'\{[\s\S]*?\}', response_text)
            if not json_match:
                return {
                    'relevance': 0.5 if len(content) > 100 else 0.0,
                    'is_complete': False,
                    'found_data': content[:200] if len(content) > 0 else '',
                    'needs_verification': True,
                    'needs_context': True,
                    'confidence': 0.3
                }
            json_str = json_match.group(0)
            fallback = {
                'relevance': 0.5 if len(content) > 100 else 0.0,
                'is_complete': False,
                'found_data': content[:200] if len(content) > 0 else '',
                'needs_verification': True,
                'needs_context': True,
                'confidence': 0.3
            }
            result = safe_json_loads(json_str, fallback, content)
            return {
                'relevance': float(result.get('relevance', 0)),
                'is_complete': bool(result.get('is_complete', False)),
                'found_data': str(result.get('found_data', '')),
                'needs_verification': bool(result.get('needs_verification', True)),
                'needs_context': bool(result.get('needs_context', True)),
                'confidence': float(result.get('confidence', 0))
            }
        except Exception as e:
            logger.error(f"Error in content assessment: {str(e)}")
            return {
                'relevance': 0.0,
                'is_complete': False,
                'found_data': '',
                'needs_verification': True,
                'needs_context': True,
                'confidence': 0.0
            }

    def extract_key_information(self, content: str, topic: str) -> Dict:
        extraction_prompt = f"""You are a precise information extractor. Extract key information from the content that is relevant to the topic.
        You must respond in valid JSON format with exactly these fields:
        {{
            "main_facts": [list of key facts as strings],
            "confidence": number between 0.0-1.0,
            "timestamp": string or null,
            "source_quality": number between 0.0-1.0
        }}

        Topic: {topic}
        Content: {content}

        Respond ONLY with the JSON object, no other text:"""

        try:
            response = invoke_model(self.llm, extraction_prompt)
            response_text = response.content.strip()
            json_match = re.search(r'\{[\s\S]*?\}', response_text)
            if not json_match:
                return {
                    "main_facts": ["Unable to extract structured information from source"],
                    "confidence": 0.0,
                    "timestamp": None,
                    "source_quality": 0.0
                }
            json_str = json_match.group(0)
            fallback = {
                "main_facts": ["Unable to extract structured information from source"],
                "confidence": 0.0,
                "timestamp": None,
                "source_quality": 0.0
            }
            info = safe_json_loads(json_str, fallback, content)
            
            if not isinstance(info.get('main_facts', []), list):
                info['main_facts'] = [str(info.get('main_facts', ''))]
            
            return {
                'main_facts': info.get('main_facts', []),
                'confidence': min(max(info.get('confidence', 0.0), 0.0), 1.0),
                'timestamp': info.get('timestamp'),
                'source_quality': min(max(info.get('source_quality', 0.0), 0.0), 1.0)
            }
        except Exception as e:
            logger.error(f"Error extracting information: {str(e)}")
            return {
                "main_facts": ["Unable to extract structured information from source"],
                "confidence": 0.0,
                "timestamp": None,
                "source_quality": 0.0
            }

    def assess_question_complexity(self, topic: str) -> float:
        complexity_prompt = f"""
        Analyze the complexity of this research topic/question.
        Rate from 0.0 to 1.0, where:
        - 0.0: Very simple
        - 0.3: Basic fact-finding
        - 0.6: Moderate complexity
        - 1.0: Complex analysis
        
        Topic: {topic}
        
        Respond with only a number between 0.0 and 1.0:"""
        
        try:
            response = invoke_model(self.llm, complexity_prompt)
            matches = re.findall(r"0?\.[0-9]+", response.content)
            if matches:
                rating = float(matches[0])
            else:
                rating = 0.5
            return min(max(rating, 0.0), 1.0)
        except Exception as e:
            logger.error(f"Error assessing question complexity: {str(e)}")
            return 0.5

    def _check_information_consistency(self, facts: List[str]) -> bool:
        return True

    def should_continue_research(self, topic: str, current_source: Dict) -> Dict:
        if topic not in self.research_memory:
            return {"continue": True, "reason": "No research started yet"}

        findings = self.research_memory[topic]
        sources_count = len(findings['sources'])
        complexity = self.assess_question_complexity(topic)
        
        min_sources = max(2, int(complexity * 5))
        quality_threshold = 0.7 + (complexity * 0.2)
        high_quality_sources = sum(1 for s in findings['sources'] 
                                   if s.get('relevance', 0) > quality_threshold 
                                   and s.get('confidence', 0) > quality_threshold)
        
        if high_quality_sources >= min_sources:
            return {"continue": False, "reason": "Sufficient high-quality sources found"}
        
        max_sources = min_sources * 2
        if sources_count >= max_sources:
            return {"continue": False, "reason": "Maximum sources reached"}
        
        if sources_count > 1:
            info_consistent = self._check_information_consistency(findings['main_facts'])
            if not info_consistent:
                return {"continue": True, "reason": "Found inconsistent information", "priority": "verification"}
        
        if sources_count > 0:
            latest_source = findings['sources'][-1]
            if latest_source.get('needs_verification', True):
                return {"continue": True, "reason": "Need verification", "priority": "verification"}
            if latest_source.get('needs_context', True) and complexity > 0.5:
                return {"continue": True, "reason": "Need context", "priority": "context"}
        
        return {"continue": True, "reason": "Need more information"}

    def brave_search_run(self, query: str, retries: int = 3) -> str:
        if not BRAVE_API_KEY:
            logger.error("Brave Search API key not set. Unable to perform search.")
            return ""
        for i in range(retries):
            try:
                return self.brave_search.run(query)
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning("Hit rate limit. Waiting before retry...")
                    time.sleep((i+1)*2)
                else:
                    logger.error(f"HTTP Error during Brave search: {str(e)}")
                    time.sleep(2)
            except Exception as ex:
                logger.error(f"Error in Brave search: {str(ex)}")
                time.sleep(2)
        return ""

    def fetch_additional_info(self, topic: str) -> str:
        self.current_topic = topic
        query_type = self.memory.categorize_query(topic)
        
        if topic not in self.research_memory:
            self.research_memory[topic] = {
                'sources': [],
                'main_facts': [],
                'last_update': time.time(),
                'visited_urls': set()
            }

        all_research = []
        research_status = {"continue": True, "reason": "Initial research"}
        
        if query_type == 'stock_price':
            priority_domains = [
                'marketwatch.com',
                'finance.yahoo.com',
                'bloomberg.com',
                'reuters.com'
            ]
            
            for domain in priority_domains:
                if any(domain in s.get('url', '') for s in self.research_memory[topic]['sources']):
                    continue
                    
                search_query = f"site:{domain} {topic}"
                search_results = self.brave_search_run(search_query)
                urls = extract_urls_from_search_results(search_results)
                
                if urls:
                    url = urls[0]
                    if url not in self.research_memory[topic]['visited_urls']:
                        self.research_memory[topic]['visited_urls'].add(url)
                        content = fetch_webpage_content(url, self.provider, topic)
                        
                        assessment = self.assess_content_relevance(content, topic)
                        if assessment['relevance'] > 0.7:
                            info = self.extract_key_information(content, topic)
                            current_source = {**assessment, **info}
                            
                            self.research_memory[topic]['sources'].append({
                                'url': url,
                                'content': content,
                                **current_source
                            })
                            self.research_memory[topic]['main_facts'].extend(info['main_facts'])
                            
                            if assessment['relevance'] > 0.8 and assessment['confidence'] > 0.8:
                                research_status = {"continue": False, "reason": "Found reliable stock price"}
                                break

        search_attempts = 0
        max_search_attempts = 3
        
        while research_status["continue"] and search_attempts < max_search_attempts:
            try:
                if search_attempts == 0:
                    search_query = topic
                elif search_attempts == 1:
                    search_query = f"{topic} latest information"
                else:
                    search_query = f"{topic} current data {datetime.now().strftime('%Y')}"

                if research_status.get("priority") == "verification":
                    search_query += " facts verify source"
                elif research_status.get("priority") == "context":
                    search_query += " background context"
                
                logger.info(f"Searching with query: {search_query}")
                results = self.brave_search_run(search_query)
                urls = extract_urls_from_search_results(results)
                
                urls = [url for url in urls if url not in self.research_memory[topic]['visited_urls']]
                
                if not urls:
                    search_attempts += 1
                    continue
                
                urls = self.memory.prioritize_urls(urls, topic)
                
                for url in urls[:2]:
                    if url in self.research_memory[topic]['visited_urls']:
                        continue
                        
                    self.research_memory[topic]['visited_urls'].add(url)
                    start_time = time.time()
                    content = fetch_webpage_content(url, self.provider, topic)
                    response_time = time.time() - start_time
                    
                    assessment = self.assess_content_relevance(content, topic)
                    domain = urlparse(url).netloc
                    
                    success = assessment['relevance'] > 0.5
                    self.memory.update_source_reliability(
                        domain=domain,
                        query_type=query_type,
                        success=success,
                        response_time=response_time,
                        content_quality=assessment['relevance']
                    )
                    
                    if success:
                        info = self.extract_key_information(content, topic)
                        current_source = {**assessment, **info}
                        
                        self.research_memory[topic]['sources'].append({
                            'url': url,
                            'content': content,
                            **current_source
                        })
                        self.research_memory[topic]['main_facts'].extend(info['main_facts'])
                        
                        research_status = self.should_continue_research(topic, current_source)
                        logger.info(f"Research status: {research_status['reason']}")
                        
                        if not research_status["continue"]:
                            break
                
                if not research_status["continue"]:
                    break
                    
                search_attempts += 1
                
            except Exception as e:
                logger.error(f"Error in research iteration: {str(e)}")
                search_attempts += 1

        all_research.append(f"""
        === Research Summary ===
        Query Type: {query_type}
        Total Sources: {len(self.research_memory[topic]['sources'])}
        Key Facts Found: {json.dumps(self.research_memory[topic]['main_facts'], indent=2)}
        Sources: {json.dumps([{
            'url': s['url'],
            'relevance': s.get('relevance', 0),
            'confidence': s.get('confidence', 0),
            'found_data': s.get('found_data', '')
        } for s in self.research_memory[topic]['sources']], indent=2)}
        """)

        return "\n\n".join(all_research)

    def generate_report(self, topic: str) -> str:
        additional_info = self.fetch_additional_info(topic)
        
        enhanced_prompt = f"""
        Generate a comprehensive report based on the research findings.
        Focus on the most relevant and current information.
        
        Topic: {topic}
        Research Findings: {additional_info}
        
        Guidelines:
        1. Prioritize information from high-quality sources
        2. Include specific, factual information
        3. Note any significant gaps or uncertainties
        4. Cite sources where appropriate
        
        Report:"""
        
        for attempt in range(self.max_retries):
            try:
                report = invoke_model(self.llm, enhanced_prompt)
                return report.content
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return f"Error generating report: {str(e)}"
                time.sleep(self.retry_delay)

    def assess_research_accuracy(self, topic: str, research_data: Dict) -> Dict:
        assessment_prompt = f"""Analyze the research results for accuracy and completeness.
        Consider:
        1. Consistency across sources
        2. Data freshness and relevance
        3. Source reliability
        4. Information completeness
        
        Topic: {topic}
        Research Data: {json.dumps(research_data, indent=2)}
        
        Respond with JSON:
        {{
            "is_accurate": boolean,
            "confidence": float,
            "completeness": float,
            "concerns": [string],
            "verification_needed": boolean
        }}"""
        
        try:
            response = invoke_model(self.llm, assessment_prompt)
            json_match = re.search(r'\{[\s\S]*?\}', response.content)
            if json_match:
                assessment = safe_json_loads(json_match.group(0), {
                    "is_accurate": False,
                    "confidence": 0.0,
                    "completeness": 0.0,
                    "concerns": ["Assessment failed"],
                    "verification_needed": True
                })
            else:
                assessment = {
                    "is_accurate": False,
                    "confidence": 0.0,
                    "completeness": 0.0,
                    "concerns": ["No JSON returned"],
                    "verification_needed": True
                }
            self.current_assessment = assessment
            return assessment
        except Exception as e:
            logger.error(f"Error in research assessment: {str(e)}")
            return {
                "is_accurate": False,
                "confidence": 0.0,
                "completeness": 0.0,
                "concerns": ["Assessment failed"],
                "verification_needed": True
            }
    
    def record_human_feedback(self, topic: str, is_accurate: bool, notes: str = None):
        if not self.current_assessment:
            logger.error("No current research assessment available")
            return
            
        sources = [s['url'] for s in self.research_memory.get(topic, {}).get('sources', [])]
        self.memory.record_feedback(
            topic=topic,
            sources=sources,
            agent_assessment=self.current_assessment,
            human_feedback=is_accurate,
            notes=notes
        )
        
        self.current_assessment = None
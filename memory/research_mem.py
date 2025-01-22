import os
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from source_reliable.source_reliability_class import SourceReliability
from config.log import logger
from typing import Dict, List


class ResearchMemory:
    def __init__(self, memory_file="agent_memory.json"):
        self.memory_file = memory_file
        self.source_reliability = {}
        self.query_patterns = {}
        self.feedback_history = {}
        self.load_memory()
    
    def load_memory(self):
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    
                    for domain, info in data.get('sources', {}).items():
                        self.source_reliability[domain] = SourceReliability(
                            domain=domain,
                            query_types=info.get('query_types', {}),
                            last_success=datetime.fromisoformat(info['last_success']) if info.get('last_success') else None,
                            last_failure=datetime.fromisoformat(info['last_failure']) if info.get('last_failure') else None,
                            total_attempts=info.get('total_attempts', 0),
                            successful_attempts=info.get('successful_attempts', 0),
                            average_response_time=info.get('average_response_time', 0.0),
                            notes=info.get('notes', [])
                        )
                    
                    self.query_patterns = data.get('query_patterns', {})
                    self.feedback_history = data.get('feedback_history', {})
                    
                logger.info(f"Loaded research memory with {len(self.source_reliability)} sources and {len(self.feedback_history)} feedback entries")
        except Exception as e:
            logger.error(f"Error loading research memory: {str(e)}")
            self.source_reliability = {}
            self.query_patterns = {}
            self.feedback_history = {}
    
    def save_memory(self):
        try:
            data = {
                'sources': {
                    domain: {
                        'query_types': info.query_types,
                        'last_success': info.last_success.isoformat() if info.last_success else None,
                        'last_failure': info.last_failure.isoformat() if info.last_failure else None,
                        'total_attempts': info.total_attempts,
                        'successful_attempts': info.successful_attempts,
                        'average_response_time': info.average_response_time,
                        'notes': info.notes
                    }
                    for domain, info in self.source_reliability.items()
                },
                'query_patterns': self.query_patterns,
                'feedback_history': self.feedback_history
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Successfully saved research memory")
        except Exception as e:
            logger.error(f"Error saving research memory: {str(e)}")
    
    def categorize_query(self, query: str) -> str:
        categories = {
            'stock_price': r'(?i)(stock|share)\s+price|price\s+of\s+stock',
            'financial_data': r'(?i)financial|revenue|earnings|profit|market\s+cap',
            'company_info': r'(?i)headquarters|ceo|founded|employees|about',
            'news': r'(?i)news|latest|recent|update|announce',
            'technical': r'(?i)technology|software|product|service|api',
            'general': r'.*'
        }
        
        for category, pattern in categories.items():
            if re.search(pattern, query):
                return category
        return 'general'
    
    def update_source_reliability(self, domain: str, query_type: str, success: bool, response_time: float, content_quality: float):
        if domain not in self.source_reliability:
            self.source_reliability[domain] = SourceReliability(
                domain=domain,
                query_types={},
                last_success=None,
                last_failure=None,
                total_attempts=0,
                successful_attempts=0,
                average_response_time=0.0,
                notes=[]
            )
        
        source = self.source_reliability[domain]
        current_time = datetime.now(timezone.utc)
        
        if query_type not in source.query_types:
            source.query_types[query_type] = 0.0
        
        source.total_attempts += 1
        if success:
            source.successful_attempts += 1
            source.last_success = current_time
            source.query_types[query_type] = (
                source.query_types[query_type] * 0.9 +
                content_quality * 0.1
            )
        else:
            source.last_failure = current_time
            source.query_types[query_type] *= 0.9
        
        source.average_response_time = (
            source.average_response_time * 0.9 +
            response_time * 0.1
        )
        
        self.save_memory()
    
    def get_best_sources(self, query_type: str, min_reliability: float = 0.3) -> List[str]:
        relevant_sources = []
        
        for domain, source in self.source_reliability.items():
            reliability = source.query_types.get(query_type, 0.0)
            if reliability >= min_reliability:
                relevant_sources.append((domain, reliability))
        
        relevant_sources.sort(key=lambda x: x[1], reverse=True)
        return [domain for domain, _ in relevant_sources]
    
    def prioritize_urls(self, urls: List[str], query: str) -> List[str]:
        query_type = self.categorize_query(query)
        self.get_best_sources(query_type)
        
        scored_urls = []
        for url in urls:
            domain = urlparse(url).netloc
            source = self.source_reliability.get(domain)
            
            if source:
                reliability = source.query_types.get(query_type, 0.0)
                success_rate = source.successful_attempts / max(1, source.total_attempts)
                response_speed = 1.0 / (1.0 + source.average_response_time)
                score = (reliability * 0.5 +
                        success_rate * 0.3 +
                        response_speed * 0.2)
            else:
                score = 0.1
            
            scored_urls.append((url, score))
        
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        return [url for url, _ in scored_urls]
    
    def record_feedback(self, topic: str, sources: List[str], agent_assessment: Dict, human_feedback: bool, notes: str = None):
        current_time = datetime.now(timezone.utc)
        query_type = self.categorize_query(topic)
        
        feedback_entry = {
            'timestamp': current_time.isoformat(),
            'topic': topic,
            'sources': sources,
            'agent_assessment': agent_assessment,
            'human_feedback': human_feedback,
            'query_type': query_type,
            'notes': notes
        }
        
        if topic not in self.feedback_history:
            self.feedback_history[topic] = []
        self.feedback_history[topic].append(feedback_entry)
        
        agent_confidence = agent_assessment.get('confidence', 0.0)
        agent_correct = agent_assessment.get('is_accurate', False)
        
        for source in sources:
            domain = urlparse(source).netloc
            if domain not in self.source_reliability:
                continue
                
            source_info = self.source_reliability[domain]
            
            if human_feedback:
                if agent_correct == human_feedback:
                    self._update_source_confidence(domain, query_type, True, 1.0)
                    source_info.notes.append(f"[{current_time.isoformat()}] Accurate assessment confirmed by human feedback")
                else:
                    self._update_source_confidence(domain, query_type, False, 1.0)
                    source_info.notes.append(f"[{current_time.isoformat()}] Assessment contradicted by human feedback")
            else:
                self._update_source_confidence(domain, query_type, agent_correct, agent_confidence)
        
        self.save_memory()
        
    def _update_source_confidence(self, domain: str, query_type: str, success: bool, confidence: float):
        source = self.source_reliability[domain]
        
        if query_type not in source.query_types:
            source.query_types[query_type] = 0.0
            
        current_reliability = source.query_types[query_type]
        
        if success:
            new_reliability = current_reliability + (1 - current_reliability) * confidence * 0.1
        else:
            new_reliability = current_reliability * 0.8
            
        source.query_types[query_type] = max(0.0, min(1.0, new_reliability))
    
    def get_feedback_stats(self, domain: str = None, query_type: str = None) -> Dict:
        stats = {
            'total_entries': 0,
            'agent_accuracy': 0.0,
            'human_agreement': 0.0,
            'query_type_performance': {},
            'recent_trends': []
        }
        
        relevant_entries = []
        
        for topic_entries in self.feedback_history.values():
            for entry in topic_entries:
                if domain and not any(domain in s for s in entry['sources']):
                    continue
                if query_type and entry['query_type'] != query_type:
                    continue
                relevant_entries.append(entry)
        
        if not relevant_entries:
            return stats
            
        stats['total_entries'] = len(relevant_entries)
        
        correct_assessments = sum(1 for e in relevant_entries 
                                if e['agent_assessment'].get('is_accurate') == e['human_feedback'])
        human_agreements = sum(1 for e in relevant_entries if e['human_feedback'])
        
        stats['agent_accuracy'] = correct_assessments / len(relevant_entries)
        stats['human_agreement'] = human_agreements / len(relevant_entries)
        
        query_types = {}
        for entry in relevant_entries:
            qt = entry['query_type']
            if qt not in query_types:
                query_types[qt] = {'total': 0, 'successful': 0}
            query_types[qt]['total'] += 1
            if entry['human_feedback']:
                query_types[qt]['successful'] += 1
        
        stats['query_type_performance'] = {
            qt: {'success_rate': data['successful'] / data['total']}
            for qt, data in query_types.items()
        }
        
        recent = relevant_entries[-10:]
        stats['recent_trends'] = [
            {
                'timestamp': e['timestamp'],
                'query_type': e['query_type'],
                'success': e['human_feedback']
            }
            for e in recent
        ]
        
        return stats
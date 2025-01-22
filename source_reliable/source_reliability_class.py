from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class SourceReliability:
    domain: str
    query_types: Dict[str, float]
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    total_attempts: int
    successful_attempts: int
    average_response_time: float
    notes: List[str]
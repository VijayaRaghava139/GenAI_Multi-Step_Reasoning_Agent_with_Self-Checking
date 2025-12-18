from typing import TypedDict, List, Dict, Any, Optional

class CheckResult(TypedDict):
    check_name: str
    passed: bool
    details: str

class AgentState(TypedDict):
    question: str
    plan: str  
    reasoning_visible_to_user: str   
    code: str                
    intermediate_results: Dict[str, Any]  
    final_answer: Optional[str]
    verification: str  
    checks: List[CheckResult]      
    retries: int
    status: str    


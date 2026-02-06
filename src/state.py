from typing import TypedDict, List, Dict, Any, Optional

class ProductInfo(TypedDict):
    target_country: str
    category: str
    product_name: str
    material: str
    function: str
    target_audience: str
    claims: str  # User's intended claims
    qualifications: List[str]  # Existing certificates

class EvidenceItem(TypedDict):
    id: str
    content: str
    source: str
    url: str
    date: str
    score: str  # High/Medium/Low
    query: str  # The query that found this evidence

class ComplianceIssue(TypedDict):
    issue: str
    risk_level: str
    severity: str
    suggestion: str
    evidence_id: str  # Refers to EvidenceItem.id

class ProhibitedExpression(TypedDict):
    original: str
    suggested: str

class ComplianceReport(TypedDict):
    risk_level: str  # RED, YELLOW, GREEN
    confidence_score: float
    issues: List[ComplianceIssue]
    required_qualifications: List[str]
    prohibited_expressions: List[ProhibitedExpression]

class Listing(TypedDict):
    title: str
    bullets: List[str]
    description: str
    faq: List[Dict[str, str]]
    video_script: Optional[str]

class ListingsCollection(TypedDict):
    version_a: Listing
    version_b: Listing
    difference_summary: List[str]

class AgentState(TypedDict):
    user_input: Dict[str, Any]
    product_info: ProductInfo
    intake_warning: Optional[str] # For category consistency check
    retrieval_queries: List[str]
    evidence: List[EvidenceItem]
    compliance_report: ComplianceReport
    market_data: Dict[str, Any]
    listings: ListingsCollection
    eval_report: Dict[str, Any]
    debug_logs: List[str]
    step_progress: str  # Current step name
    metrics: Dict[str, float] # For cost/time tracking

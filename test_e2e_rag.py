import json
from src.services.srs_generation_service import SRSGenerationService
from src.services.analysis_service import AnalysisService
from src.services.clarification_service import ClarificationService
from src.llm.factory import create_llm_provider
from src.core.config import Settings
from src.db.database import Database
from src.db.models import Base, Project
from sqlalchemy.orm import sessionmaker
from src.schemas.project import generate_uuid
from src.schemas.clarification import ClarificationAnswerSubmission, ClarificationAnswerItem

# Setup with real Ollama
settings = Settings()
settings.llm_provider = 'ollama'
settings.rag_enabled = True
settings.ollama_timeout_seconds = 1800  # 30 minutes for SRS generation
settings.llm_timeout_seconds = 1800
settings.llm_max_retries = 2  # Allow more retries for SRS

# Create DB
db = Database(settings.database_url)
db.init_db()
Session = sessionmaker(bind=db.engine, autoflush=False, expire_on_commit=False)
session = Session()

provider = create_llm_provider(settings)

# Create a test project - College firewall (eval-001)
p = Project(
    id=generate_uuid(), 
    name='College Firewall', 
    description='I want to build a firewall and network monitoring system for a college campus with separate student, faculty, laboratory and administrative networks.', 
    status='draft'
)
session.add(p)
session.commit()
print('Project created:', p.id)

# Run analysis
analysis_svc = AnalysisService(session, provider)
result = analysis_svc.analyse_project(p.id)
print('Analysis categories:', result.analysis.inferred_categories)
print('Missing info:', result.analysis.missing_information)

# Run clarification
clarification_svc = ClarificationService(session, provider)
clar_result = clarification_svc.generate_questions(p.id)
print('Clarifications:', len(clar_result.questions))
for q in clar_result.questions:
    print('  -', q.question_text)

# Submit answers
answers = []
for q in clar_result.questions:
    answers.append(ClarificationAnswerItem(question_id=q.id, answer_text='100', skipped=False))
clarification_svc.submit_answers(p.id, ClarificationAnswerSubmission(answers=answers))
print('Answers submitted')

# Generate SRS with RAG
srs_svc = SRSGenerationService(session, provider, settings)
srs_result = srs_svc.generate_srs(p.id, use_rag=True)
print('SRS version:', srs_result.version_number)

# Get the full SRS
version = srs_svc.get_version(p.id, srs_result.version_id)
srs = version.srs
print('SRS generated:', srs is not None)
if srs:
    print('Requirements:', len(srs.functional_requirements), 'functional,', len(srs.security_requirements), 'security')
    print('Threats:', len(srs.threats))
    print('Source refs in first func req:', len(srs.functional_requirements[0].source_references) if srs.functional_requirements else 0)
    gen_meta = srs.generation_metadata
    print('Gen metadata:', gen_meta)
    if gen_meta:
        print('  RAG enabled:', gen_meta.get('rag_enabled'))
        print('  Retrieved chunks:', gen_meta.get('retrieved_chunks'))
        print('  KB version:', gen_meta.get('kb_version'))
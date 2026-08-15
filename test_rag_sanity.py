from src.rag.retrieval import create_retriever
from src.rag.chromadb_client import create_chromadb_client
from src.rag.embedding_provider import create_embedding_provider
from src.core.config import Settings

settings = Settings()
settings.embedding_provider = 'ollama'
settings.ollama_base_url = 'http://127.0.0.1:11434'
settings.embedding_model = 'nomic-embed-text'
settings.rag_top_k = 10
settings.rag_min_score = 0.3

chroma = create_chromadb_client(settings)
embedding = create_embedding_provider(settings)
retriever = create_retriever(settings, chroma, embedding)

test_queries = [
    ('firewall network segmentation', {'inferred_categories': ['CAT-02', 'CAT-03'], 'goals': ['Block malicious traffic', 'Monitor network traffic'], 'constraints': ['Campus network infrastructure']}),
    ('OAuth API security', {'inferred_categories': ['CAT-05'], 'goals': ['Authenticate API requests', 'Rate limiting', 'Input validation'], 'constraints': ['Low latency', 'OWASP API Top 10']}),
    ('identity MFA RBAC', {'inferred_categories': ['CAT-04'], 'goals': ['Single sign-on', 'Multi-factor authentication', 'Role-based access'], 'constraints': ['Existing directory integration', 'Audit trail']}),
]

for query_name, context in test_queries:
    print('\n=== ' + query_name + ' ===')
    result = retriever.retrieve(context, 'test-kb-v1')
    print('Total chunks: ' + str(result.total_chunks))
    print('Retrieval time: ' + str(result.retrieval_time_ms) + ' ms')
    for i, chunk in enumerate(result.chunks[:3]):
        meta = chunk.metadata
        title = meta.get('document_title', 'N/A')
        org = meta.get('organisation', 'N/A')
        section = meta.get('section_heading', 'N/A')
        print('  Chunk ' + str(i) + ': id=' + chunk.chunk_id + ', score=' + str(chunk.relevance_score) + ', title=' + title + ', org=' + org + ', section=' + section)
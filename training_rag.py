"""
Enhanced RAG Training System for Oreplot
Uses vector embeddings for automatic document learning and retrieval.
"""

import os
import json
import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from database import get_db_session
from models import TrainingEmbedding, TrainingStats

EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
MAX_CHUNKS_PER_QUERY = 5
SIMILARITY_THRESHOLD = 0.5
MIN_RESULTS_FALLBACK = 2
MAX_PARALLEL_EMBEDDINGS = 3


def get_openai_client():
    """Get OpenAI client with API key"""
    import openai
    # Check Replit AI Integrations first, then fallback to standard key
    api_key = os.environ.get('AI_INTEGRATIONS_OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    
    base_url = os.environ.get('AI_INTEGRATIONS_OPENAI_BASE_URL')
    if base_url:
        return openai.OpenAI(api_key=api_key, base_url=base_url)
    return openai.OpenAI(api_key=api_key)


def create_embedding(text: str) -> Optional[List[float]]:
    """Create embedding vector for text using OpenAI"""
    client = get_openai_client()
    if not client:
        return None
    
    try:
        text = text.replace("\n", " ").strip()
        if not text:
            return None
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding error: {e}")
        return None


def create_embedding_for_chunk(args: Tuple[int, str]) -> Tuple[int, str, Optional[List[float]]]:
    """Create embedding for a single chunk (for parallel processing)"""
    chunk_index, chunk_text = args
    embedding = create_embedding(chunk_text)
    return (chunk_index, chunk_text, embedding)


def create_embeddings_parallel(chunks: List[str], progress_callback=None) -> List[Tuple[int, str, Optional[List[float]]]]:
    """Create embeddings for multiple chunks in parallel"""
    results = []
    total = len(chunks)
    
    chunk_args = [(i, chunk) for i, chunk in enumerate(chunks)]
    
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_EMBEDDINGS) as executor:
        futures = {executor.submit(create_embedding_for_chunk, args): args[0] for args in chunk_args}
        completed = 0
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            
            if progress_callback:
                progress = 0.4 + (0.5 * (completed / total))
                progress_callback(progress, f"Embedding chunk {completed}/{total}...")
    
    results.sort(key=lambda x: x[0])
    return results


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks for better retrieval"""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        if end < text_length:
            break_point = text.rfind('\n\n', start, end)
            if break_point == -1 or break_point <= start:
                break_point = text.rfind('\n', start, end)
            if break_point == -1 or break_point <= start:
                break_point = text.rfind('. ', start, end)
            if break_point != -1 and break_point > start:
                end = break_point + 1
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 50:
            chunks.append(chunk)
        
        start = end - overlap if end < text_length else text_length
    
    return chunks


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if not vec1 or not vec2:
        return 0.0
    
    a = np.array(vec1)
    b = np.array(vec2)
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def generate_file_id(file_bytes: bytes, file_name: str) -> str:
    """Generate a unique file ID based on content hash and filename"""
    content_hash = hashlib.md5(file_bytes).hexdigest()[:8]
    return f"{file_name}_{content_hash}"


def process_training_document(
    file_bytes: bytes,
    file_name: str,
    file_type: str,
    category: str,
    commodity: str,
    user_id: int,
    progress_callback=None
) -> Dict:
    """
    Process a training document: extract text, chunk it, and create embeddings.
    
    Returns:
        Dict with processing results
    """
    from document_extractor import DocumentExtractor
    
    unique_file_id = generate_file_id(file_bytes, file_name)
    
    result = {
        'success': False,
        'file_name': file_name,
        'file_id': unique_file_id,
        'chunks_created': 0,
        'error': None
    }
    
    try:
        if progress_callback:
            progress_callback(0.1, "Extracting text...")
        
        if file_type.lower() == 'pdf':
            extracted_text = DocumentExtractor.extract_text_from_pdf(file_bytes)
        elif file_type.lower() == 'docx':
            extracted_text = DocumentExtractor.extract_text_from_docx(file_bytes)
        elif file_type.lower() in ['xlsx', 'xls']:
            extracted_text = DocumentExtractor.extract_text_from_xlsx(file_bytes)
        elif file_type.lower() in ['csv', 'txt']:
            extracted_text = DocumentExtractor.extract_text_from_txt(file_bytes)
        elif file_type.lower() in ['png', 'jpg', 'jpeg', 'tif']:
            extracted_text = DocumentExtractor.extract_text_from_image(file_bytes)
        elif file_type.lower() == 'xml':
            extracted_text = file_bytes.decode('utf-8', errors='ignore')
        else:
            result['error'] = f"Unsupported file type: {file_type}"
            return result
        
        if not extracted_text or len(extracted_text) < 100:
            result['error'] = "Could not extract sufficient text from document"
            return result
        
        if progress_callback:
            progress_callback(0.3, "Chunking document...")
        
        chunks = chunk_text(extracted_text)
        
        if not chunks:
            result['error'] = "No valid chunks created from document"
            return result
        
        if progress_callback:
            progress_callback(0.4, f"Creating embeddings for {len(chunks)} chunks (parallel mode: {MAX_PARALLEL_EMBEDDINGS} concurrent)...")
        
        embedding_results = create_embeddings_parallel(chunks, progress_callback)
        
        embeddings_created = 0
        
        with get_db_session() as db:
            for chunk_index, chunk_text_content, embedding in embedding_results:
                if embedding:
                    training_embedding = TrainingEmbedding(
                        file_name=unique_file_id,
                        file_type=file_type,
                        file_size=len(file_bytes),
                        chunk_index=chunk_index,
                        chunk_text=chunk_text_content,
                        chunk_tokens=len(chunk_text_content.split()),
                        category=category,
                        commodity=commodity,
                        embedding=embedding,
                        embedding_model=EMBEDDING_MODEL,
                        chunk_metadata={
                            'total_chunks': len(chunks),
                            'original_length': len(extracted_text),
                            'original_filename': file_name
                        },
                        uploaded_by=user_id
                    )
                    db.add(training_embedding)
                    embeddings_created += 1
            
            db.commit()
            
            update_training_stats(db)
        
        if progress_callback:
            progress_callback(1.0, "Complete!")
        
        result['success'] = True
        result['chunks_created'] = embeddings_created
        result['total_chunks'] = len(chunks)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def update_training_stats(db):
    """Update global training statistics"""
    try:
        total_chunks = db.query(TrainingEmbedding).count()
        
        from sqlalchemy import func
        total_tokens = db.query(func.sum(TrainingEmbedding.chunk_tokens)).scalar() or 0
        
        file_sizes = db.query(
            TrainingEmbedding.file_name,
            func.max(TrainingEmbedding.file_size).label('size')
        ).group_by(TrainingEmbedding.file_name).all()
        total_size = sum(fs.size or 0 for fs in file_sizes)
        
        unique_files = len(file_sizes)
        
        category_counts = {}
        categories = db.query(TrainingEmbedding.category, func.count(TrainingEmbedding.id)).group_by(TrainingEmbedding.category).all()
        for cat, count in categories:
            if cat:
                category_counts[cat] = count
        
        commodity_counts = {}
        commodities = db.query(TrainingEmbedding.commodity, func.count(TrainingEmbedding.id)).group_by(TrainingEmbedding.commodity).all()
        for com, count in commodities:
            if com:
                commodity_counts[com] = count
        
        stats = db.query(TrainingStats).first()
        if not stats:
            stats = TrainingStats()
            db.add(stats)
        
        stats.total_documents = unique_files
        stats.total_chunks = total_chunks
        stats.total_tokens = total_tokens
        stats.total_size_bytes = total_size
        stats.categories_count = category_counts
        stats.commodities_count = commodity_counts
        stats.last_upload_at = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        print(f"Error updating training stats: {e}")


def retrieve_relevant_training(
    query_text: str,
    category: Optional[str] = None,
    commodity: Optional[str] = None,
    limit: int = MAX_CHUNKS_PER_QUERY,
    threshold: float = SIMILARITY_THRESHOLD
) -> List[Dict]:
    """
    Retrieve the most relevant training chunks for a given query.
    
    Args:
        query_text: The text to find relevant training for
        category: Filter by category (optional)
        commodity: Filter by commodity (optional)
        limit: Maximum number of results
        threshold: Minimum similarity threshold
    
    Returns:
        List of relevant training chunks with similarity scores
    """
    query_embedding = create_embedding(query_text[:8000])
    if not query_embedding:
        return []
    
    try:
        with get_db_session() as db:
            query = db.query(TrainingEmbedding)
            
            if category:
                query = query.filter(TrainingEmbedding.category == category)
            if commodity:
                query = query.filter(TrainingEmbedding.commodity == commodity)
            
            all_embeddings = query.all()
            
            if not all_embeddings:
                return []
            
            all_results = []
            for emb in all_embeddings:
                if emb.embedding:
                    similarity = cosine_similarity(query_embedding, emb.embedding)
                    all_results.append({
                        'id': emb.id,
                        'chunk_text': emb.chunk_text,
                        'file_name': emb.file_name,
                        'category': emb.category,
                        'commodity': emb.commodity,
                        'similarity': float(similarity)
                    })
            
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            results = [r for r in all_results if r['similarity'] >= threshold]
            
            if len(results) < MIN_RESULTS_FALLBACK and len(all_results) >= MIN_RESULTS_FALLBACK:
                results = all_results[:MIN_RESULTS_FALLBACK]
            
            stats = db.query(TrainingStats).first()
            if stats:
                stats.last_training_used_at = datetime.utcnow()
                db.commit()
            
            return results[:limit]
            
    except Exception as e:
        print(f"Error retrieving training: {e}")
        return []


def normalize_filter(value: Optional[str]) -> Optional[str]:
    """Normalize category/commodity filter values"""
    if not value:
        return None
    value = value.strip().lower()
    if value in ('all', 'general', 'any', ''):
        return None
    return value


def build_enhanced_context(
    document_text: str,
    category: Optional[str] = None,
    commodity: Optional[str] = None
) -> str:
    """
    Build enhanced context by retrieving relevant training content.
    
    Args:
        document_text: The document being analyzed
        category: Filter training by category
        commodity: Filter training by commodity
    
    Returns:
        Enhanced context string to prepend to prompts
    """
    if not document_text or len(document_text) < 100:
        return ""
    
    client = get_openai_client()
    if not client:
        return ""
    
    normalized_category = normalize_filter(category)
    normalized_commodity = normalize_filter(commodity)
    
    sample = document_text[:8000] if len(document_text) > 8000 else document_text
    sample = ' '.join(sample.split())
    
    try:
        relevant_chunks = retrieve_relevant_training(
            query_text=sample,
            category=normalized_category,
            commodity=normalized_commodity,
            limit=3,
            threshold=0.5
        )
    except Exception:
        return ""
    
    if not relevant_chunks:
        return ""
    
    context_parts = [
        "=== TRAINING REFERENCE MATERIAL ===",
        "The following are examples from similar mining technical documents that demonstrate accurate data extraction patterns:",
        ""
    ]
    
    for i, chunk in enumerate(relevant_chunks, 1):
        context_parts.append(f"--- Reference {i} (from {chunk['file_name']}, similarity: {chunk['similarity']:.0%}) ---")
        text = chunk['chunk_text']
        if len(text) > 2000:
            text = text[:2000] + "..."
        context_parts.append(text)
        context_parts.append("")
    
    context_parts.append("=== END TRAINING REFERENCE ===")
    context_parts.append("Use these reference patterns to guide accurate extraction from the document below.")
    context_parts.append("")
    
    return "\n".join(context_parts)


def get_training_statistics() -> Dict:
    """Get current training system statistics"""
    try:
        with get_db_session() as db:
            stats = db.query(TrainingStats).first()
            
            if not stats:
                return {
                    'total_documents': 0,
                    'total_chunks': 0,
                    'total_tokens': 0,
                    'total_size_mb': 0,
                    'categories': {},
                    'commodities': {},
                    'last_upload': None,
                    'last_used': None
                }
            
            return {
                'total_documents': stats.total_documents or 0,
                'total_chunks': stats.total_chunks or 0,
                'total_tokens': stats.total_tokens or 0,
                'total_size_mb': round((stats.total_size_bytes or 0) / (1024 * 1024), 2),
                'categories': stats.categories_count or {},
                'commodities': stats.commodities_count or {},
                'last_upload': stats.last_upload_at.isoformat() if stats.last_upload_at else None,
                'last_used': stats.last_training_used_at.isoformat() if stats.last_training_used_at else None
            }
    except Exception as e:
        print(f"Error getting training stats: {e}")
        return {
            'total_documents': 0,
            'total_chunks': 0,
            'total_tokens': 0,
            'total_size_mb': 0,
            'categories': {},
            'commodities': {},
            'last_upload': None,
            'last_used': None,
            'error': str(e)
        }


def delete_training_document(file_name: str) -> bool:
    """Delete all training embeddings for a specific document"""
    try:
        with get_db_session() as db:
            deleted = db.query(TrainingEmbedding).filter(
                TrainingEmbedding.file_name == file_name
            ).delete(synchronize_session='fetch')
            db.commit()
            
            if deleted > 0:
                update_training_stats(db)
            
            return deleted > 0
    except Exception as e:
        print(f"Error deleting training document: {e}")
        return False


def delete_all_training() -> bool:
    """Delete all training data"""
    try:
        with get_db_session() as db:
            db.query(TrainingEmbedding).delete()
            
            stats = db.query(TrainingStats).first()
            if stats:
                stats.total_documents = 0
                stats.total_chunks = 0
                stats.total_tokens = 0
                stats.total_size_bytes = 0
                stats.categories_count = {}
                stats.commodities_count = {}
            
            db.commit()
            return True
    except Exception as e:
        print(f"Error deleting all training: {e}")
        return False


def get_training_documents() -> List[Dict]:
    """Get list of all training documents with stats"""
    try:
        with get_db_session() as db:
            from sqlalchemy import func
            
            docs = db.query(
                TrainingEmbedding.file_name,
                TrainingEmbedding.file_type,
                TrainingEmbedding.category,
                TrainingEmbedding.commodity,
                func.count(TrainingEmbedding.id).label('chunks'),
                func.sum(TrainingEmbedding.chunk_tokens).label('tokens'),
                func.max(TrainingEmbedding.file_size).label('size'),
                func.max(TrainingEmbedding.created_at).label('uploaded_at')
            ).group_by(
                TrainingEmbedding.file_name,
                TrainingEmbedding.file_type,
                TrainingEmbedding.category,
                TrainingEmbedding.commodity
            ).order_by(func.max(TrainingEmbedding.created_at).desc()).all()
            
            return [{
                'file_name': d.file_name,
                'file_type': d.file_type,
                'category': d.category,
                'commodity': d.commodity,
                'chunks': d.chunks,
                'tokens': d.tokens or 0,
                'size_mb': round((d.size or 0) / (1024 * 1024), 2),
                'uploaded_at': d.uploaded_at.isoformat() if d.uploaded_at else None
            } for d in docs]
            
    except Exception as e:
        print(f"Error getting training documents: {e}")
        return []

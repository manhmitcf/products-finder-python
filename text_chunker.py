import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

class TextChunker:
    """
    Utility class for chunking long text into smaller, semantically meaningful pieces
    """
    
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        """
        Initialize the text chunker
        
        Args:
            chunk_size: Maximum number of characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using Vietnamese sentence patterns
        """
        # Vietnamese sentence endings
        sentence_endings = r'[.!?](?:\s|$)'
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks
        
        Returns:
            List of dictionaries containing chunk text and metadata
        """
        if not text or len(text) <= self.chunk_size:
            return [{"text": self.clean_text(text), "chunk_id": 0, "start_pos": 0}]
        
        text = self.clean_text(text)
        chunks = []
        
        # Try to split by sentences first for better semantic coherence
        sentences = self.split_by_sentences(text)
        
        if len(sentences) > 1:
            # Group sentences into chunks
            current_chunk = ""
            chunk_id = 0
            start_pos = 0
            
            for sentence in sentences:
                # If adding this sentence would exceed chunk size, save current chunk
                if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "chunk_id": chunk_id,
                        "start_pos": start_pos
                    })
                    
                    # Start new chunk with overlap
                    overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                    current_chunk = overlap_text + " " + sentence
                    start_pos = len(text) - len(current_chunk)
                    chunk_id += 1
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            # Add the last chunk
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk.strip(),
                    "chunk_id": chunk_id,
                    "start_pos": start_pos
                })
        else:
            # Fallback to character-based chunking
            for i in range(0, len(text), self.chunk_size - self.overlap):
                chunk_text = text[i:i + self.chunk_size]
                chunks.append({
                    "text": chunk_text,
                    "chunk_id": i // (self.chunk_size - self.overlap),
                    "start_pos": i
                })
        
        return chunks
    
    def chunk_product_description(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create chunks for a product's description with metadata
        
        Args:
            product: Product dictionary containing description info
            
        Returns:
            List of chunk documents ready for vector storage
        """
        description = product.get('descriptioninfo', '')
        if not description:
            return []
        
        chunks = self.chunk_text(description)
        chunked_products = []
        
        for chunk in chunks:
            # Create a new document for each chunk
            chunk_doc = {
                # Core product info
                'product_id': product.get('data_product'),
                'name': product.get('name'),
                'url': product.get('url'),
                'brand': product.get('brand'),
                'category_name': product.get('category_name'),
                'price': product.get('price'),
                'market_price': product.get('market_price'),
                'average_rating': product.get('average_rating'),
                
                # Chunk-specific info
                'chunk_text': chunk['text'],
                'chunk_id': chunk['chunk_id'],
                'chunk_start_pos': chunk['start_pos'],
                'is_chunk': True,
                
                # Original full description for reference
                'full_description': description[:200] + "..." if len(description) > 200 else description,
                
                # For search display
                'descriptioninfo': chunk['text']  # This will be used for vector search
            }
            
            chunked_products.append(chunk_doc)
        
        return chunked_products

def process_products_with_chunking(products: List[Dict[str, Any]], 
                                 model: SentenceTransformer,
                                 chunk_size: int = 300, 
                                 overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Process a list of products, creating chunks and embeddings
    
    Args:
        products: List of product dictionaries
        model: SentenceTransformer model for creating embeddings
        chunk_size: Maximum characters per chunk
        overlap: Overlap between chunks
        
    Returns:
        List of processed documents with embeddings
    """
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
    all_documents = []
    
    print(f"Processing {len(products)} products with chunking...")
    
    for i, product in enumerate(products):
        if i % 100 == 0:
            print(f"Processed {i}/{len(products)} products")
        
        # Get chunks for this product
        chunks = chunker.chunk_product_description(product)
        
        if chunks:
            # Create embeddings for each chunk
            chunk_texts = [chunk['chunk_text'] for chunk in chunks]
            embeddings = model.encode(chunk_texts)
            
            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk['description_vector'] = embedding.tolist()
                all_documents.append(chunk)
        else:
            # If no description, create a minimal document
            minimal_doc = {
                'product_id': product.get('data_product'),
                'name': product.get('name'),
                'url': product.get('url'),
                'brand': product.get('brand'),
                'category_name': product.get('category_name'),
                'price': product.get('price'),
                'market_price': product.get('market_price'),
                'average_rating': product.get('average_rating'),
                'chunk_text': product.get('name', ''),
                'chunk_id': 0,
                'is_chunk': False,
                'descriptioninfo': product.get('name', ''),
                'description_vector': model.encode([product.get('name', '')]).tolist()[0]
            }
            all_documents.append(minimal_doc)
    
    print(f"Created {len(all_documents)} document chunks from {len(products)} products")
    return all_documents

def aggregate_search_results(results: List[Dict[str, Any]], max_products: int = 5) -> List[Dict[str, Any]]:
    """
    Aggregate chunked search results back to product level
    
    Args:
        results: List of search results (chunks)
        max_products: Maximum number of unique products to return
        
    Returns:
        List of aggregated product results
    """
    # Group results by product_id
    product_groups = {}
    
    for result in results:
        product_id = result.get('product_id')
        if product_id not in product_groups:
            product_groups[product_id] = []
        product_groups[product_id].append(result)
    
    # Aggregate each product group
    aggregated_results = []
    
    for product_id, chunks in product_groups.items():
        if len(aggregated_results) >= max_products:
            break
            
        # Find the best chunk (highest score)
        best_chunk = max(chunks, key=lambda x: x.get('score', 0))
        
        # Create aggregated result
        aggregated_result = {
            'product_id': product_id,
            'name': best_chunk.get('name'),
            'url': best_chunk.get('url'),
            'brand': best_chunk.get('brand'),
            'category_name': best_chunk.get('category_name'),
            'price': best_chunk.get('price'),
            'market_price': best_chunk.get('market_price'),
            'average_rating': best_chunk.get('average_rating'),
            'score': best_chunk.get('score'),
            
            # Combine relevant chunks for description
            'descriptioninfo': best_chunk.get('chunk_text', ''),
            'relevant_chunks': [chunk.get('chunk_text', '') for chunk in chunks[:3]],  # Top 3 chunks
            'total_chunks_found': len(chunks)
        }
        
        aggregated_results.append(aggregated_result)
    
    # Sort by score
    aggregated_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return aggregated_results[:max_products]
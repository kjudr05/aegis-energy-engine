# backend/core_math/rag_engine.py
import chromadb
from sentence_transformers import SentenceTransformer
import os

class LocalAegisRAG:
    def __init__(self):
        # 1. Initialize a completely local, persistent database on disk
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "chroma_db")
        
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        
        # 2. Load a lightweight, high-accuracy embedding model (runs completely offline)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 3. Create or fetch our specialized geopolitical intelligence collection
        self.collection = self.chroma_client.get_or_create_collection(name="geopolitical_intel")
        
        # Seed the database if it's currently empty
        if self.collection.count() == 0:
            self._seed_intel_database()

    def _seed_intel_database(self):
        """Seeds the local vector store with real-world context data records."""
        intel_dossier = [
            {
                "id": "doc_lloyds_premium_01",
                "text": "Lloyd's Joint War Committee Clause JWC-2026: Any verified kinetic, drone, or boarding threat level exceeding an intensity profile of 0.70 inside the Strait of Hormuz automatically triggers a mandatory 300% premium hike on marine hull insurance for commercial tankers traversing the Persian Gulf."
            },
            {
                "id": "doc_unclos_straits_02",
                "text": "UNCLOS Article 38 Transit Passage: In high-risk military escalation scenarios within chokepoints, international law guarantees transit passage. However, state-sponsored boarding actions or dark ship profiles constitute a material breach of maritime safety, nullifying safe sovereign passage protections."
            },
            {
                "id": "doc_spr_protocol_03",
                "text": "Emergency Fuel Security Mandate: When national Strategic Petroleum Reserves fall below a critical consumption threshold of 5.0 days, industrial refinery infrastructure must prioritize immediate volume guarantees and asset preservation over standard spot-market price variations."
            }
        ]
        
        # Generate mathematical embeddings and save them into Chroma DB
        for doc in intel_dossier:
            embedding = self.embedding_model.encode(doc["text"]).tolist()
            self.collection.add(
                documents=[doc["text"]],
                embeddings=[embedding],
                ids=[doc["id"]]
            )
        print("Aegis Geopolitical Intel Vector Database initialized and seeded successfully.")

    def query_intel(self, query_text: str, n_results: int = 1) -> str:
        """Performs a vector search to pull relevant documentation based on semantics."""
        query_vector = self.embedding_model.encode(query_text).tolist()
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results
        )
        
        if results and results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0][0]
        return "No specific maritime regulatory clause found for current context vector."

# Test execution block to verify setup
if __name__ == "__main__":
    rag = LocalAegisRAG()
    sample_search = "What happens to insurance premiums if a threat happens at Hormuz?"
    print(f"\nQuery: {sample_search}")
    print(f"Retrieved Fact: {rag.query_intel(sample_search)}")
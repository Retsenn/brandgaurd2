# ============================================================================
# retrive.py — RAG Retrieval (Knowledge Base se Relevant Info Nikalna)
# ============================================================================
# YEH FILE KYA KARTI HAI?
# -----------------------
# Jab AI ko kisi post ko evaluate karna hai, use pehle company ki guidelines
# chahiye as context. Ye file:
#   1. Query (post ka text) leta hai
#   2. ChromaDB mein similar chunks dhundhta hai (similarity search)
#   3. Relevant guidelines return karta hai taaki AI unke basis pe judge kare
#
# RAG KYA HAI? (Detailed)
# ────────────────────────
# RAG = Retrieval-Augmented Generation
#
# Step 1 (RETRIEVAL): Apne database se relevant documents dhundho
#   Query: "Is our logo blue or red?"
#   Database finds: "Official brand color: Pantone 286C (Royal Blue)"
#
# Step 2 (AUGMENTED): Retrieved docs ko AI ke prompt mein add karo
#   Prompt = "Given these guidelines: [Royal Blue is official color]
#            Evaluate this post: [post with red logo]"
#
# Step 3 (GENERATION): AI answer generate kare with context
#   AI: "Logo color is incorrect. Guidelines say Royal Blue, but post uses Red."
#
# BINA RAG KE:
#   AI: "The logo looks fine." (kyunki use company ki specific guidelines nahi pata)
#
# SIMILARITY SEARCH KYA HAI?
# ──────────────────────────
# Embedding vectors ke beech distance calculate karo.
# Jo vectors paas hain (kam distance) = similar meaning.
# ChromaDB ye automatically karta hai jab hum query karte hain.
# ============================================================================

import os
import chromadb
from chromadb.config import Settings

# ─── CHROMADB CONNECTION ────────────────────────────────────────────────────
# Same ChromaDB database se connect karo jo ingest.py ne create ki thi

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")

chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

# Collection lo (ingest.py ne already bana di hogi)
collection = chroma_client.get_or_create_collection(
    name="brand_guidelines",
    metadata={"description": "Brand guidelines, product facts, and legal rules"}
)


def retrieve_relevant_guidelines(query_text, n_results=5):
    """
    Query ke basis pe relevant brand guidelines dhundho.
    
    YEH FUNCTION RAG KA "R" (RETRIEVAL) HAI!
    
    PARAMETERS:
        query_text: str — post ka text ya search query
        n_results: int — kitne relevant chunks chahiye (default 5)
    
    RETURNS:
        list of dicts, har ek mein:
            - text: chunk ka content
            - source: kaunsi file se aaya
            - doc_type: document type
            - relevance_score: kitna relevant hai (0-1, lower = more relevant)
    
    KAISE KAAM KARTA HAI:
    1. ChromaDB query_text ka embedding banata hai (internally)
    2. Saare stored embeddings se distance calculate karta hai
    3. Sabse kam distance wale (= sabse similar) chunks return karta hai
    """
    # Pehle check karo ki collection mein kuch hai ya nahi
    if collection.count() == 0:
        print("⚠️ Knowledge base is empty! Please ingest documents first.")
        return []
    
    # ChromaDB se similar chunks dhundho
    # ──────────────────────────────────
    results = collection.query(
        query_texts=[query_text],  # Kya dhundhna hai
        n_results=min(n_results, collection.count()),  # Kitne results chahiye
        # include → results mein kya kya chahiye
        include=["documents", "metadatas", "distances"]
    )
    # ChromaDB internally:
    #   1. query_text ka embedding banata hai
    #   2. Saare stored embeddings se cosine distance calculate karta hai
    #   3. Sabse kam distance wale n chunks return karta hai
    
    # Results ko clean format mein convert karo
    # ──────────────────────────────────────────
    guidelines = []
    
    if results and results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            doc_text = results["documents"][0][i]
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            
            guidelines.append({
                "text": doc_text,
                "source": metadata.get("filename", "Unknown"),
                "doc_type": metadata.get("doc_type", "unknown"),
                "chunk_index": metadata.get("chunk_index", 0),
                "relevance_score": round(distance, 4),
                # Distance: lower = more relevant
                # 0.0 = exact match, 1.0+ = not very relevant
            })
    
    return guidelines


def format_guidelines_for_prompt(guidelines):
    """
    Retrieved guidelines ko ek formatted string mein convert karo
    jo AI prompt mein daal sake.
    
    YEH FUNCTION RAG KA "A" (AUGMENTED) HAI!
    
    INPUT:
        guidelines: list — retrieve_relevant_guidelines() ka output
    
    OUTPUT:
        str — formatted guidelines text for the AI prompt
    
    EXAMPLE OUTPUT:
        --- GUIDELINE 1 (from: brand_rules.pdf, type: guideline) ---
        Our brand voice is professional yet approachable. We use...
        
        --- GUIDELINE 2 (from: product_facts.txt, type: factsheet) ---
        Product X was launched in 2025. It supports up to...
    """
    if not guidelines:
        return "No specific guidelines found in the knowledge base for this content."
    
    formatted_parts = []
    
    for i, g in enumerate(guidelines, 1):
        # enumerate(list, 1) → (1, item1), (2, item2), ... numbering 1 se start
        part = (
            f"--- GUIDELINE {i} (source: {g['source']}, "
            f"type: {g['doc_type']}) ---\n"
            f"{g['text']}"
        )
        formatted_parts.append(part)
    
    return "\n\n".join(formatted_parts)
    # "\n\n".join() → saare parts ko double newline se jodo


def retrieve_and_format(query_text, n_results=5):
    """
    One-step function: relevant guidelines dhundho AUR format karo.
    
    Ye convenience function hai — evaluate.py is ek function ko call karega
    instead of do alag functions.
    
    PARAMETERS:
        query_text: str — post ka text
        n_results: int — kitne chunks chahiye
    
    RETURNS:
        tuple: (formatted_string, raw_guidelines_list)
    """
    raw_guidelines = retrieve_relevant_guidelines(query_text, n_results)
    formatted_text = format_guidelines_for_prompt(raw_guidelines)
    
    return formatted_text, raw_guidelines


def search_knowledge_base(query, n_results=10):
    """
    Knowledge base mein search karo — admin dashboard ke liye.
    Ye retrieve_relevant_guidelines jaisa hi hai but zyada results deta hai
    aur UI-friendly format mein.
    """
    return retrieve_relevant_guidelines(query, n_results=n_results)

import os
import networkx as nx
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Storage file paths
GRAPH_FILE = "tn_graph.graphml"
CHROMA_DIR = "./chroma_db"

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# ---------------------------------------------------------
# 1. Load or Build Knowledge Graph & Vector Store
# ---------------------------------------------------------
def get_or_build_indices():
    # If both already exist on disk, reload them immediately
    if os.path.exists(GRAPH_FILE) and os.path.exists(CHROMA_DIR):
        print("Found existing cached graph and vector database. Loading from disk...")
        G = nx.read_graphml(GRAPH_FILE)
        vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        return G, vectorstore

    print("Cache not found. Scraping website and extracting knowledge graph via OpenAI...")
    url = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="
    loader = WebBaseLoader(
        web_paths=[url],
        header_template={"User-Agent": "Mozilla/5.0"}
    )
    docs = loader.load()

    for doc in docs:
        doc.page_content = "\n".join([line.strip() for line in doc.page_content.splitlines() if line.strip()])

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    split_docs = text_splitter.split_documents(docs)[:6]

    # Save Vector Store
    vectorstore = Chroma.from_documents(
        split_docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    # Extract Graph
    allowed_nodes = ["Scheme", "Department", "Beneficiary", "Benefit", "EligibilityCriteria"]
    allowed_relationships = ["ADMINISTERED_BY", "TARGETS_BENEFICIARY", "PROVIDES_BENEFIT", "REQUIRES_ELIGIBILITY"]

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=allowed_nodes,
        allowed_relationships=allowed_relationships,
        strict_mode=True
    )
    
    graph_docs = transformer.convert_to_graph_documents(split_docs)

    G = nx.DiGraph()
    for g_doc in graph_docs:
        for node in g_doc.nodes:
            G.add_node(str(node.id), type=str(node.type))
        for rel in g_doc.relationships:
            G.add_edge(str(rel.source.id), str(rel.target.id), relation=str(rel.type))

    # Persist NetworkX Graph to disk (GraphML preserves node/edge attributes)
    nx.write_graphml(G, GRAPH_FILE)
    print(f"Graph persisted to '{GRAPH_FILE}'.")
    return G, vectorstore

G, vectorstore = get_or_build_indices()
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
print(f"Ready: Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.\n")

# ---------------------------------------------------------
# 2. Dynamic Entity Extractor
# ---------------------------------------------------------
class ExtractedEntities(BaseModel):
    entities: list[str] = Field(
        description="Key entities, organization names, schemes, agriculture terms, or topics mentioned in the query."
    )

entity_extractor_llm = llm.with_structured_output(ExtractedEntities)

def extract_entities(query: str) -> list[str]:
    prompt = f"Identify all key entities, departments, schemes, crops, or topics in this query: '{query}'"
    try:
        res = entity_extractor_llm.invoke(prompt)
        return res.entities
    except Exception:
        return [w for w in query.split() if len(w) > 3]

# ---------------------------------------------------------
# 3. Multi-Hop Graph Traversal
# ---------------------------------------------------------
def get_multihop_subgraph_facts(graph: nx.DiGraph, query_entities: list[str], max_hops: int = 2) -> str:
    matched_nodes = set()
    for entity in query_entities:
        for node in graph.nodes:
            if entity.lower() in node.lower() or node.lower() in entity.lower():
                matched_nodes.add(node)

    if not matched_nodes:
        return "No direct graph entities found."

    triplets = []
    for start_node in matched_nodes:
        sub = nx.ego_graph(graph.to_undirected(), start_node, radius=max_hops)
        for u, v in sub.edges():
            if graph.has_edge(u, v):
                rel = graph[u][v].get("relation", "RELATED_TO")
                u_type = graph.nodes[u].get("type", "Entity")
                v_type = graph.nodes[v].get("type", "Entity")
                triplets.append(f"({u} [{u_type}]) -[:{rel}]-> ({v} [{v_type}])")
            elif graph.has_edge(v, u):
                rel = graph[v][u].get("relation", "RELATED_TO")
                u_type = graph.nodes[u].get("type", "Entity")
                v_type = graph.nodes[v].get("type", "Entity")
                triplets.append(f"({v} [{v_type}]) -[:{rel}]-> ({u} [{u_type}])")

    unique_triplets = list(dict.fromkeys(triplets))
    return "\n".join(unique_triplets[:15]) if unique_triplets else "No direct graph entities found."

# ---------------------------------------------------------
# 4. Hybrid Graph RAG Query
# ---------------------------------------------------------
qa_prompt = ChatPromptTemplate.from_template(
    """You are an agricultural welfare assistant for Tamil Nadu government schemes.
Answer the question accurately using the provided structured graph facts and document context.

Structured Knowledge Graph Facts:
{graph_context}

Document Context:
{text_context}

Question: {question}

Answer:"""
)

rag_chain = qa_prompt | llm | StrOutputParser()

def answer_query(user_query: str):
    detected_entities = extract_entities(user_query)
    graph_context = get_multihop_subgraph_facts(G, detected_entities, max_hops=2)
    
    vector_docs = retriever.invoke(user_query)
    text_context = "\n\n".join([d.page_content for d in vector_docs])

    print(f"\n[Extracted Entities]: {detected_entities}")
    print(f"[Graph Triplet Sample]:\n{graph_context[:250]}...\n" if len(graph_context) > 250 else f"[Graph Triplet Sample]:\n{graph_context}\n")

    return rag_chain.invoke({
        "graph_context": graph_context,
        "text_context": text_context,
        "question": user_query
    })

# ---------------------------------------------------------
# 5. Interactive Chat Loop
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print(" Tamil Nadu Scheme Hybrid Graph RAG Assistant ")
    print(" Type your question below, or type 'exit' or 'quit' to stop.")
    print("=" * 60)

    while True:
        try:
            query = input("\nAsk a question: ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Exiting chat. Goodbye!")
                break
            
            print("\nSearching graph & vector index...")
            answer = answer_query(query)
            print("\nResponse:")
            print(answer)
            print("-" * 60)
        except KeyboardInterrupt:
            print("\nExiting chat. Goodbye!")
            break
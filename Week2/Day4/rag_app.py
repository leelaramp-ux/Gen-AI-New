import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="Multi-PDF RAG with MMR", layout="wide")
st.title("📚 Multi-PDF RAG Assistant with Diverse Sources (MMR)")

if not os.getenv("OPENAI_API_KEY"):
    st.error("Missing `OPENAI_API_KEY`. Please set it in your environment.")
    st.stop()

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("1. Document Ingestion")
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )
    build_index_btn = st.button("Build Vector Database", type="primary")

    if build_index_btn and uploaded_files:
        with st.spinner("Processing & indexing..."):
            all_docs = []
            for file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file.getbuffer())
                    tmp_path = tmp.name

                try:
                    loader = PyPDFLoader(tmp_path)
                    docs = loader.load()
                    for d in docs:
                        d.metadata["source_file"] = file.name
                        d.metadata["page_number"] = d.metadata.get("page", 0) + 1
                    all_docs.extend(docs)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
            split_chunks = splitter.split_documents(all_docs)

            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            st.session_state.vector_store = FAISS.from_documents(split_chunks, embeddings)
            st.session_state.total_chunks = len(split_chunks)
            st.session_state.processed_files = [f.name for f in uploaded_files]

        st.success(f"Indexed {st.session_state.total_chunks} chunks!")

    # ----------------- RETRIEVAL TUNING CONTROLS -----------------
    st.divider()
    st.header("2. Retrieval Settings")
    retrieval_strategy = st.radio(
        "Search Mode",
        options=["Maximal Marginal Relevance (MMR)", "Similarity with Score Threshold"],
        help="MMR diversifies chunks to avoid duplicate citations. Threshold cuts out off-topic text."
    )

    k_chunks = st.slider("Number of Chunks to Retrieve (k)", min_value=2, max_value=10, value=4)

    if retrieval_strategy == "Maximal Marginal Relevance (MMR)":
        lambda_mult = st.slider(
            "Diversity vs Relevance (lambda)",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.05,
            help="1.0 = Pure similarity, 0.0 = Maximum diversity."
        )
        fetch_k = st.slider(
            "Candidate Pool (fetch_k)",
            min_value=k_chunks,
            max_value=30,
            value=15,
            help="Number of initial candidates to evaluate for MMR."
        )
    else:
        # Distance score in FAISS (L2 / cosine distance: smaller = closer)
        score_threshold = st.slider(
            "Relevance Score Cutoff",
            min_value=0.2,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Drops chunks that fall below this similarity score."
        )

# ----------------- MAIN PANEL -----------------
if st.session_state.vector_store is None:
    st.info("👈 Upload PDF files and click **Build Vector Database** to begin.")
else:
    query = st.text_input("Ask a question across your documents:")

    if query:
        # Configure retriever dynamically based on sidebar controls
        if retrieval_strategy == "Maximal Marginal Relevance (MMR)":
            retriever = st.session_state.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": k_chunks,
                    "fetch_k": fetch_k,
                    "lambda_mult": lambda_mult
                }
            )
        else:
            retriever = st.session_state.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": k_chunks,
                    "score_threshold": score_threshold
                }
            )

        with st.spinner("Searching and synthesizing..."):
            retrieved_docs = retriever.invoke(query)

            if not retrieved_docs:
                st.warning("No relevant snippets passed the relevance threshold. Try rephrasing or adjusting the search settings.")
            else:
                # Format context
                context_blocks = []
                for i, doc in enumerate(retrieved_docs, start=1):
                    src = doc.metadata.get("source_file", "Unknown")
                    pg = doc.metadata.get("page_number", "?")
                    context_blocks.append(f"[Snippet {i} | File: {src} | Page: {pg}]\n{doc.page_content.strip()}")

                formatted_context = "\n\n---\n\n".join(context_blocks)

                prompt = ChatPromptTemplate.from_messages([
                    ("system", (
                        "You are a strict research assistant answering questions using retrieved context from multiple documents.\n\n"
                        "Rules:\n"
                        "1. Answer ONLY using the provided snippets.\n"
                        "2. If documents contradict or disagree, explicitly state: 'File A claims X while File B claims Y'.\n"
                        "3. Do not invent details not present in the snippets."
                    )),
                    ("human", "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:")
                ])

                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                chain = prompt | llm | StrOutputParser()
                answer = chain.invoke({"context": formatted_context, "question": query})

                # Display Results
                st.subheader("Answer")
                st.markdown(answer)

                st.divider()
                st.subheader("Attributed Sources")
                unique_sources = set(
                    (d.metadata.get("source_file", "Unknown"), d.metadata.get("page_number", "?"))
                    for d in retrieved_docs
                )
                for src_file, pg in sorted(unique_sources):
                    st.markdown(f"- 📄 `{src_file}` (Page {pg})")

                with st.expander("Inspect Retrieved Snippets"):
                    for idx, doc in enumerate(retrieved_docs, 1):
                        st.markdown(f"**Snippet {idx} — {doc.metadata.get('source_file')} (Page {doc.metadata.get('page_number')})**")
                        st.text(doc.page_content)
                        st.markdown("---")
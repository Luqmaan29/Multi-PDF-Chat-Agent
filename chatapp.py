import os
import streamlit as st
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import base64

# LangChain & Google GenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import google.generativeai as genai

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# -----------------------------
# Helper Functions
# -----------------------------
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            st.warning(f"⚠️ Could not read {pdf.name}: {e}")
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=50000, chunk_overlap=1000)
    return text_splitter.split_text(text)

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context.
    - If the answer is not in the provided context, reply with:
      "Answer is not available in the context."
    - Do not make up information.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()
    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
    st.write("**Reply:**", response["output_text"])

# -----------------------------
# Helper to set background
# -----------------------------
def set_bg_local(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()

    st.markdown(
        f"""
        <style>
        /* Main app background */
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #000000 !important;  /* Main screen text black */
        }}

        /* Gradient overlay animation */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: linear-gradient(-45deg, #ff6f61, #f7b32b, #6a2c70, #b83b5e);
            background-size: 400% 400%;
            animation: gradientBG 20s ease infinite;
            opacity: 0.15;
            z-index: -1;
        }}

        @keyframes gradientBG {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}

        /* Main header animation */
        .stHeader {{
            color: #000000 !important;
            font-size: 42px;
            font-weight: bold;
            text-shadow: 1px 1px 2px #ffffff;
            animation: floatHeader 4s ease-in-out infinite;
        }}
        @keyframes floatHeader {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}

        /* Sidebar styling */
        .css-1d391kg {{
            background-color: rgba(20, 20, 20, 0.85);
            padding: 20px;
            border-radius: 15px;
            animation: fadeIn 1.5s ease forwards;
            opacity: 0;
            color: #ffffff !important;  /* Keep sidebar text white */
        }}

        /* Button styling */
        .stButton>button {{
            background-color: #FF6F61;
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 10px 20px;
        }}
        .stButton>button:hover {{
            background-color: #FF3B2E;
            color: white;
        }}

        /* Input styling */
        input[type="text"] {{
            border-radius: 10px;
            padding: 10px;
            font-size: 18px;
        }}
        .stTextInput {{
            animation: fadeIn 1.5s ease forwards;
            opacity: 0;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0px); }}
        }}

        /* Footer */
        .footer {{
            position: fixed;
            bottom: 0; left: 0; width: 100%;
            background-color: rgba(0,0,0,0.7);
            padding: 15px; text-align: center;
            color: #000000 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Streamlit App
# -----------------------------
def main():
    st.set_page_config("Multi PDF Chatbot", page_icon=":scroll:", layout="wide")
    set_bg_local("img/bg.jpg")

    # Header
    st.markdown("<h1 class='stHeader'>📚 Multi-PDF Chat Agent 🤖</h1>", unsafe_allow_html=True)

    # User query input
    user_question = st.text_input("Ask a Question from the uploaded PDF files:")
    if user_question:
        user_input(user_question)

    # Sidebar
    with st.sidebar:
        st.image("img/Robot.jpg", use_container_width=True)
        st.write("---")
        st.title("📁 PDF Upload Section")
        pdf_docs = st.file_uploader("Upload your PDF Files & Click on 'Submit & Process'", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing... ⏳"):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Processing Complete ✅")

    # Footer
    st.markdown(
        """
        <div class='footer'>
            © <a href="#" target="_blank" style="color: #000000;">Mohammed Luqmaan</a>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    main()

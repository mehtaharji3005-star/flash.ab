from datetime import datetime
import io
from io import BytesIO
import json
import os
import re
import tempfile

from docx import Document
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredPowerPointLoader,
)
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd
from pptx import Presentation
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
import streamlit as st

# Streamlit Page Setup
st.set_page_config(page_title="Flashcard generator for notes", page_icon="📖", layout="wide")
st.image("bg.png")

# Sidebar Setup
st.sidebar.title("API Configuration")
st.sidebar.subheader("Provide Required API Keys")

GOOGLE_API_KEY = st.sidebar.text_input("GOOGLE_API_KEY", type="password")

if not GOOGLE_API_KEY:
    st.error("❌ Please provide the GOOGLE_API_KEY in the sidebar to proceed.")
    st.stop()
else:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    st.sidebar.success("✅ API key loaded successfully.")

# Display Banner Image from local file
if os.path.exists("bg.png"):
    st.image("bg.png", use_container_width=True)
else:
    st.title("Flashcard Generator for Notes ✈️ 🚗")

# Initialize LLM Model
model = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    google_api_key=GOOGLE_API_KEY
)

# Helper function to extract text from uploaded files
def process_uploaded_files(uploaded_files):
    combined_text = ""
    for uploaded_file in uploaded_files:
        suffix = os.path.splitext(uploaded_file.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        try:
            if suffix == ".pdf":
                loader = PyPDFLoader(tmp_path)
            elif suffix == ".docx":
                loader = Docx2txtLoader(tmp_path)
            elif suffix == ".pptx":
                loader = UnstructuredPowerPointLoader(tmp_path)
            elif suffix == ".txt":
                loader = TextLoader(tmp_path)
            else:
                st.warning(f"Unsupported file format: {uploaded_file.name}")
                continue

            docs = loader.load()
            for doc in docs:
                combined_text += doc.page_content + "\n"

        except Exception as e:
            st.error(f"Error reading file {uploaded_file.name}: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return combined_text

# PDF Generation Function
def flashcards_to_pdf(flashcards_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    for line in flashcards_text.split("\n"):
        if line.strip():
            story.append(Paragraph(line.replace(" ", "&nbsp;"), styles["BodyText"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer

# Prompt Template & Chain definition
flashcard_prompt = ChatPromptTemplate.from_template(
    """You are an advanced AI Flashcard Generator.
    Analyze the following study content carefully and generate structured, high-quality Q&A flashcards.

    Format each flashcard clearly as:
    Front: [Question or Concept]
    Back: [Answer or Explanation]

    Study Notes:
    {context}
    """
)

flashcard_chain = flashcard_prompt | model | StrOutputParser()

# UI Layout for Inputs
tab1, tab2 = st.tabs(["📄 Upload Files", "✏️ Input Text Notes"])

extracted_text = ""

with tab1:
    uploaded_files = st.file_uploader(
        "Upload PDF, DOCX, PPTX, or TXT files",
        type=["pdf", "docx", "pptx", "txt"],
        accept_multiple_files=True
    )
    if uploaded_files:
        with st.spinner("Processing files..."):
            extracted_text = process_uploaded_files(uploaded_files)
            if extracted_text.strip():
                st.success("Files processed successfully!")

with tab2:
    manual_notes = st.text_area(
        "Enter or Paste Notes",
        height=250,
        placeholder="Paste your study notes here..."
    )
    if manual_notes.strip():
        extracted_text = manual_notes

# Flashcard Generation Action
if st.button("Generate Flashcards", type="primary"):
    if not extracted_text.strip():
        st.warning("Please upload a file or enter study notes first.")
    else:
        with st.spinner("Generating Flashcards..."):
            try:
                flashcards = flashcard_chain.invoke({"context": extracted_text})
                st.session_state["flashcards_result"] = flashcards
                st.success("Flashcards Generated Successfully!")
            except Exception as e:
                st.error(f"Error generating flashcards: {e}")

# Render Results and Download Buttons
if "flashcards_result" in st.session_state and st.session_state["flashcards_result"]:
    flashcards_output = st.session_state["flashcards_result"]

    st.markdown("## 📚 Generated Flashcards")
    st.divider()
    st.markdown(flashcards_output)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download as TXT",
            data=flashcards_output,
            file_name="flashcards.txt",
            mime="text/plain"
        )
    with col2:
        pdf_buffer = flashcards_to_pdf(flashcards_output)
        st.download_button(
            label="📄 Download as PDF",
            data=pdf_buffer,
            file_name="Flashcards.pdf",
            mime="application/pdf"
        )

import os
import io
import json
import re
import tempfile
from datetime import datetime
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from docx import Document
from pptx import Presentation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredPowerPointLoader


model = ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash-lite",
    google_api_key = os.environ["GOOGLE_API_KEY"]
)
response=model.invoke("hello buddy")
print(response.content)

flashcard_prompt = ChatPromptTemplate.from_template("""You are an advanced AI Flashcard Generator. Accept study notes uploaded by the user in PDF (.pdf), Microsoft Word (.docx), PowerPoint (.pptx), and Plain Text (.txt) formats. Automatically detect the uploaded file type, extract all readable text while preserving the document structure as much as possible, clean unnecessary formatting, split the content into meaningful chunks, and process it to generate high-quality flashcards. If multiple files are uploaded, combine and organize their content before generating flashcards. If a file is empty, corrupted, password-protected, or unsupported, display a clear and user-friendly error message asking the user to upload a valid PDF, DOCX, PPTX, or TXT file. Ensure the extracted content is accurate before passing it to the AI model for flashcard generation.""")
print("done")

flashcard_chain = (
    flashcard_prompt
    | model
    | StrOutputParser()

)

if st.button("Generate Flashcards"):
    if extracted_text.strip():
        with st.spinner("Generating Flashcards..."):
            try:
                flashcards = flashcard_chain.invoke(
                    {"context": extracted_text}
                )

                if not isinstance(flashcards, str):
                    flashcards = str(flashcards)

                st.success("Flashcards Generated Successfully!")
                st.markdown("## 📚 Generated Flashcards")
                st.divider()
                st.markdown(flashcards, unsafe_allow_html=False)

            except Exception as e:
                st.error(f"Error: {e}")

    else:
        st.warning("Please upload a PDF, DOCX, PPTX, or TXT file first.")

def generate_flashcards(chain, extracted_text):
    if not extracted_text or not extracted_text.strip():
        st.warning("Please upload a PDF, DOCX, PPTX, or TXT file first.")
        return

    try:
        with st.spinner("Generating Flashcards..."):
            flashcards = chain.invoke({"context": extracted_text})

        if not isinstance(flashcards, str):
            flashcards = str(flashcards)

        st.success("Flashcards Generated Successfully!")
        st.markdown("## 📚 Generated Flashcards")
        st.divider()
        st.markdown(flashcards)

        return flashcards

    except Exception as e:
        st.exception(e)
        return None

if st.button("Generate Flashcards"):
    flashcards = generate_flashcards(
        flashcard_chain,
        extracted_text
    )

st.title("📚 AI Flashcard Generator")

sample_notes = st.text_area(
    "Enter or Paste Notes",
    height=300,
    value="""
Python is a high-level programming language.
It is interpreted, object-oriented, and easy to learn.
Variables are used to store data.
Functions are reusable blocks of code.
Lists, Tuples, Dictionaries, and Sets are Python collections.
"""
)

if st.button("Test Flashcard Generator"):
    flashcards = generate_flashcards(
        flashcard_chain,
        sample_notes
    )

    if flashcards:
        st.download_button(
            "📥 Download Flashcards",
            flashcards,
            file_name="flashcards.txt",
            mime="text/plain"
        )
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def flashcards_to_pdf(flashcards):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = []

    for line in flashcards.split("\n"):
        if line.strip():
            story.append(Paragraph(line.replace(" ", "&nbsp;"), styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)

    return buffer

if st.button("Generate Flashcards"):
    flashcards = generate_flashcards(
        flashcard_chain,
        notes
    )

    if flashcards:
        pdf = flashcards_to_pdf(flashcards)

        st.download_button(
            label="📄 Download Flashcards as PDF",
            data=pdf,
            file_name="Flashcards.pdf",
            mime="application/pdf"
        )

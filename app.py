from flask import Flask, request, render_template, jsonify
import os
import shutil
from PyPDF2 import PdfReader
from dotenv import load_dotenv

import openai

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
VECTORSTORE_FOLDER = 'docs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VECTORSTORE_FOLDER'] = VECTORSTORE_FOLDER


# pre-app startup
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(VECTORSTORE_FOLDER):
    os.makedirs(VECTORSTORE_FOLDER)
else:
    shutil.rmtree(VECTORSTORE_FOLDER)  # clean up vectorstore docs

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.environ['OPENAI_API_KEY']


# in-memory storage
splits = None
vectordb = None


# helper functions
def get_uploaded_files():
    return os.listdir(UPLOAD_FOLDER)


def has_uploaded_files():
    return len(get_uploaded_files()) > 0


def count_words_and_pages_in_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        num_words = 0
        num_pages = len(reader.pages)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                num_words += len(text.split())
        return num_words, num_pages


def split_pdf(file_path):
    loaders = [PyPDFLoader(file_path)]
    docs = []
    for loader in loaders:
        docs.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=25
    )
    global splits
    splits = text_splitter.split_documents(docs)
    return len(splits)


def presist_to_vectordb():
    global splits, vectordb
    embedding = OpenAIEmbeddings()
    vectordb = Chroma.from_documents(
        documents=splits,
        embedding=embedding,
        persist_directory=VECTORSTORE_FOLDER
    )
    vectordb.persist()
    return vectordb._collection.count()


def retrieve(question):
    # Wrap the vectorstore
    global vectordb

    # Build prompt
    template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible. Always say "thanks for asking!" at the end of the answer. 
    {context}
    Question: {question}
    Helpful Answer:"""
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

    if vectordb is not None:
        llm = OpenAI(temperature=0)
        # Run chain
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=vectordb.as_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
        )
        result = qa_chain({"query": question})
        return result["result"]

    return ""


# Flask app handlers
@app.route('/', methods=['GET', 'POST'])
def home():
    success_message = None
    if request.method == 'POST':
        file = request.files['pdf_file']
        if file and file.filename.endswith('.pdf'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            success_message = f'File {file.filename} uploaded successfully!'
    files = get_uploaded_files()
    show_upload_form = not has_uploaded_files()
    return render_template('home.html', success_message=success_message, files=files, show_upload_form=show_upload_form)


@app.route('/load/<filename>', methods=['GET'])
def process_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        word_count, page_count = count_words_and_pages_in_pdf(file_path)
        return jsonify({'filename': filename, 'word_count': word_count, 'page_count': page_count})
    else:
        return jsonify({'error': 'File not found'}), 404


@app.route('/split/<filename>', methods=['GET'])
def split_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        split_count = split_pdf(file_path)
        return jsonify({'filename': filename, 'split_count': split_count})
    else:
        return jsonify({'error': 'File not found'}), 404


@app.route('/persist/<filename>', methods=['GET'])
def persist_file(filename):
    vectordb_doc_count = presist_to_vectordb()
    return jsonify({'filename': filename, 'vectordb_doc_count': vectordb_doc_count})


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message')
    bot_response = retrieve(user_message)
    return bot_response


if __name__ == '__main__':
    app.run(debug=True)

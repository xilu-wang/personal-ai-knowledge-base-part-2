from flask import Flask, request, render_template, jsonify
import os
from PyPDF2 import PdfReader


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# helper functions
def get_uploaded_files():
    return os.listdir(UPLOAD_FOLDER)


def has_uploaded_files():
    return len(get_uploaded_files()) > 0


def count_words_in_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        num_words = 0
        for page in reader.pages:
            text = page.extract_text()
            if text:  # Check if text is extracted
                num_words += len(text.split())
        return num_words


# Flask app handlers
@app.route('/process/<filename>', methods=['GET'])
def process_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        word_count = count_words_in_pdf(file_path)
        return jsonify({'filename': filename, 'word_count': word_count})
    else:
        return jsonify({'error': 'File not found'}), 404


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


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form.get('message')
    bot_response = f"Bot: I got your message - '{user_message}'. How can I help you?"
    return bot_response


if __name__ == '__main__':
    app.run(debug=True)

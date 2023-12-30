// JavaScript for handling chat
async function sendMessage() {
    let message = document.getElementById('chat-message').value;
    let chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div>You: ${message}</div>`;

    let response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `message=${encodeURIComponent(message)}`
    });

    let botMessage = await response.text();
    chatBox.innerHTML += `<div>${botMessage}</div>`;
    document.getElementById('chat-message').value = ''; // Clear input
}

function showUploadForm() {
    document.getElementById('upload-container').classList.remove('hidden');
}

async function processFile(filename) {
    let response = await fetch(`/process/${filename}`);
    if (response.ok) {
        let data = await response.json();
        alert(`File: ${data.filename}\nWord Count: ${data.word_count}`);
    } else {
        alert('Error processing file.');
    }
}

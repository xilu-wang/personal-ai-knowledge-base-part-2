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
    let progressBar = document.getElementById(`progress-${filename}`);
    progressBar.classList.remove('hidden');
    progressBar.querySelector('.progress').style.width = '10%';

    let logOutput = document.getElementById(`log-${filename}`);
    logOutput.classList.remove('hidden');
    logOutput.innerHTML = 'Starting to process the file...';

    let hasError = false

    // step 1: load file
    logOutput.innerHTML = 'Loading the file...';
    let response = await fetch(`/load/${filename}`);
    if (response.ok) {
        let data = await response.json();
        progressBar.querySelector('.progress').style.width = '30%';
        logOutput.innerHTML = `<br> File loaded:<br>Page Count: ${data.page_count}<br>Word Count: ${data.word_count}`;
    } else {
        hasError = true
        logOutput.innerHTML = 'Error loading file. Please retry.';
    }


    // step 2: Split file
    setTimeout(async () => {
        if (!hasError) {
            logOutput.innerHTML = 'Splitting the content...';
            let response = await fetch(`/split/${filename}`);
            if (response.ok) {
                let data = await response.json();
                progressBar.querySelector('.progress').style.width = '50%';
                logOutput.innerHTML = `<br> File splitted:<br>Splits Count: ${data.split_count}`;
            } else {
                hasError = true
                logOutput.innerHTML = 'Error splitting file. Please retry.';
            }
        }
    }, 2000); // wait for 2 seconds to execute


    // step 2: persist to vectordb
    setTimeout(async () => {
        if (!hasError) {
            logOutput.innerHTML = 'Persisting the splits to vector db...';
            let response = await fetch(`/persist/${filename}`);
            if (response.ok) {
                let data = await response.json();
                progressBar.querySelector('.progress').style.width = '90%';
                logOutput.innerHTML = `<br> File persisted:<br>Doc Count: ${data.vectordb_doc_count}`;
            } else {
                hasError = true
                logOutput.innerHTML = 'Error persisting file. Please retry.';
            }
        }
    }, 5000); // wait for 5 seconds to execute


    // // complete or error out
    // progressBar.classList.add('hidden');
    // progressBar.querySelector('.progress').style.width = '0%'; // Reset for next time
}

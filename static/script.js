document.addEventListener("DOMContentLoaded", function() {
    let dropArea = document.getElementById('drop-area');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropArea.classList.add('highlight');
    }

    function unhighlight(e) {
        dropArea.classList.remove('highlight');
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        let dt = e.dataTransfer;
        let files = dt.files;

        let input = dropArea.querySelector('input[type=file]');
        input.files = files;
        updateFileList();
    }

    function updateFileList() {
        let input = document.querySelector('input[type=file]');
        let fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        for (let i = 0; i < input.files.length; i++) {
            let file = input.files[i];
            let li = document.createElement('li');
            li.textContent = file.name;
            fileList.appendChild(li);
        }
    }
});

function admin() {
    pw = prompt('パスワードを入力してください');
    if (pw == '1234') {
        window.location.href = '/admin';
    }
    else {
        alert('パスワードが異なります')
    }
}

function uploaded() {
    window.location.href = '/uploaded';
}

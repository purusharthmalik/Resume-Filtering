document.addEventListener("DOMContentLoaded", function() {
    const uploadBox = document.getElementById("upload-box");
    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name-display");

    uploadBox.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadBox.classList.add("dragover");
    });

    uploadBox.addEventListener("dragleave", () => {
        uploadBox.classList.remove("dragover");
    });

    uploadBox.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadBox.classList.remove("dragover");
        const files = event.dataTransfer.files;
        fileInput.files = files;
        displayFileName(files);
    });

    uploadBox.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        const files = fileInput.files;
        displayFileName(files);
    });

    function displayFileName(files) {
        const fileNames = Array.from(files).map(file => file.name).join(", ");
        fileNameDisplay.textContent = fileNames || "No file chosen";
    }
});

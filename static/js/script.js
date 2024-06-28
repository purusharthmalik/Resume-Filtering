document.addEventListener("DOMContentLoaded", function() {
    const uploadBox = document.getElementById("upload-box");
    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name-display");
    const uploadBtn = document.getElementById("uploadBtn");
    const processingGif = document.getElementById("processingGif");

    uploadBtn.classList.add("faded");

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
        uploadBtn.classList.remove("faded");
    });

    uploadBox.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", () => {
        const files = fileInput.files;
        displayFileName(files);
        uploadBtn.classList.remove("faded");
    });

    uploadBtn.addEventListener("click", function() {
        uploadBtn.classList.add("faded");
        processingGif.style.display = "inline";
        uploadBtn.querySelector('span').textContent = " Processing";    
    });

    function displayFileName(files) {
        const fileNames = Array.from(files).map(file => file.name).join(", ");
        fileNameDisplay.textContent = fileNames || "No file chosen";
    }
});


// Form JS
document.addEventListener("DOMContentLoaded", function() {
    const sections = document.querySelectorAll(".form-section");
    const nextButtons = document.querySelectorAll(".next-btn");
    const prevButtons = document.querySelectorAll(".prev-btn");
    const progressBar = document.querySelector(".progress-bar");
    let currentSectionIndex = 0;

    sections[currentSectionIndex].classList.add("active");
    updateProgressBar();

    nextButtons.forEach((button, index) => {
        button.addEventListener("click", () => {
            if (validateSection(sections[currentSectionIndex])) {
                sections[currentSectionIndex].classList.remove("active");
                currentSectionIndex = Math.min(currentSectionIndex + 1, sections.length - 1);
                sections[currentSectionIndex].classList.add("active");
                updateProgressBar();
            }
        });
    });

    prevButtons.forEach((button, index) => {
        button.addEventListener("click", () => {
            sections[currentSectionIndex].classList.remove("active");
            currentSectionIndex = Math.max(currentSectionIndex - 1, 0);
            sections[currentSectionIndex].classList.add("active");
            updateProgressBar();
        });
    });

    function updateProgressBar() {
        const progress = (currentSectionIndex + 1) / sections.length * 100;
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute("aria-valuenow", progress);
    }

    function validateSection(section) {
        const inputs = section.querySelectorAll("input, textarea");
        for (const input of inputs) {
            if (!input.checkValidity()) {
                input.reportValidity();
                // Change to false if data validation is needed for every field
                return true;
            }
        }
        return true;
    }
});

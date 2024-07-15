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


// JS for adding and removing fields
document.addEventListener('DOMContentLoaded', function() {
    const progressBar = document.querySelector('.progress-bar');
    const formSections = document.querySelectorAll('.form-section');
    const nextButtons = document.querySelectorAll('.next-btn');
    const prevButtons = document.querySelectorAll('.prev-btn');
    const addExperienceButton = document.querySelector('.add-experience-btn');
    const addProjectButton = document.querySelector('.add-project-btn');
    const addAchievementButton = document.querySelector('.add-achievement-btn');
    const addEducationButton = document.querySelector('.add-education-btn');
    const addCertificationButton = document.querySelector('.add-certification-btn');
    const addLanguageButton = document.querySelector('.add-language-btn');
    let currentSectionIndex = 0;

    function showSection(index) {
        formSections.forEach((section, i) => {
            section.style.display = i === index ? 'block' : 'none';
        });
        const progress = (index / (formSections.length - 1)) * 100;
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
    }

    nextButtons.forEach((button, index) => {
        button.addEventListener('click', () => {
            if (currentSectionIndex < formSections.length - 1) {
                currentSectionIndex++;
                showSection(currentSectionIndex);
            }
        });
    });

    prevButtons.forEach((button, index) => {
        button.addEventListener('click', () => {
            if (currentSectionIndex > 0) {
                currentSectionIndex--;
                showSection(currentSectionIndex);
            }
        });
    });

    addExperienceButton.addEventListener('click', () => {
        const workExperienceContainer = document.getElementById('workExperience');
        const experienceCount = workExperienceContainer.getElementsByClassName('experience-entry').length;
        const newExperience = document.createElement('div');
        newExperience.className = 'experience-entry';
        newExperience.innerHTML = `
            <div class="form-group">
                <label for="companyName${experienceCount}">Company Name:</label>
                <input type="text" class="form-control" id="companyName${experienceCount}" name="companyName${experienceCount}" required>
            </div>
            <div class="form-group">
                <label for="modeOfWork${experienceCount}">Mode of Work:</label>
                <input type="text" class="form-control" id="modeOfWork${experienceCount}" name="modeOfWork${experienceCount}" required>
            </div>
            <div class="form-group">
                <label for="jobRole${experienceCount}">Job Role:</label>
                <input type="text" class="form-control" id="jobRole${experienceCount}" name="jobRole${experienceCount}" required>
            </div>
            <div class="form-group">
                <label for="jobType${experienceCount}">Job Type:</label>
                <input type="text" class="form-control" id="jobType${experienceCount}" name="jobType${experienceCount}" required>
            </div>
            <div class="form-group">
                <label for="startDate${experienceCount}">Start Date:</label>
                <input type="date" class="form-control" id="startDate${experienceCount}" name="startDate${experienceCount}" required>
            </div>
            <div class="form-group">
                <label for="endDate${experienceCount}">End Date:</label>
                <input type="date" class="form-control" id="endDate${experienceCount}" name="endDate${experienceCount}" required>
            </div>
            <button type="button" class="btn btn-danger remove-experience-btn">Remove</button>
        `;
        workExperienceContainer.appendChild(newExperience);
        attachRemoveButtons();
    });

    addProjectButton.addEventListener('click', () => {
        const projectDetailsContainer = document.getElementById('projectDetails');
        const projectCount = projectDetailsContainer.getElementsByClassName('project-entry').length;
        const newProject = document.createElement('div');
        newProject.className = 'project-entry';
        newProject.innerHTML = `
            <div class="form-group">
                <label for="projectName${projectCount}">Project Name:</label>
                <input type="text" class="form-control" id="projectName${projectCount}" name="projectName${projectCount}" required>
            </div>
            <div class="form-group">
                <label for="projectDescription${projectCount}">Description:</label>
                <textarea id="projectDescription${projectCount}" class="form-control" name="projectDescription${projectCount}" rows="4" required></textarea>
            </div>
            <div class="form-group">
                <label for="projectStart${projectCount}">Start Date:</label>
                <input type="date" class="form-control" id="projectStart${projectCount}" name="projectStart${projectCount}" required>
            </div>
            <div class="form-group">
                <label for="projectEnd${projectCount}">End Date:</label>
                <input type="date" class="form-control" id="projectEnd${projectCount}" name="projectEnd${projectCount}" required>
            </div>
            <button type="button" class="btn btn-danger remove-project-btn">Remove</button>
        `;
        projectDetailsContainer.appendChild(newProject);
        attachRemoveButtons();
    });

    addAchievementButton.addEventListener('click', () => {
        const achievementsContainer = document.getElementById('achievements');
        const achievementCount = achievementsContainer.getElementsByClassName('achievement-entry').length;
        const newAchievement = document.createElement('div');
        newAchievement.className = 'achievement-entry';
        newAchievement.innerHTML = `
            <div class="form-group">
                <label for="achievementHeading${achievementCount}">Heading:</label>
                <input type="text" class="form-control" id="achievementHeading${achievementCount}" name="achievementHeading${achievementCount}" required>
            </div>
            <div class="form-group">
                <label for="achievementDescription${achievementCount}">Description:</label>
                <textarea id="achievementDescription${achievementCount}" class="form-control" name="achievementDescription${achievementCount}" rows="4" required></textarea>
            </div>
            <div class="form-group">
                <label for="achievementStartDate${achievementCount}">Start Date:</label>
                <input type="date" class="form-control" id="achievementStartDate${achievementCount}" name="achievementStartDate${achievementCount}" required>
            </div>
            <div class="form-group">
                <label for="achievementEndDate${achievementCount}">End Date:</label>
                <input type="date" class="form-control" id="achievementEndDate${achievementCount}" name="achievementEndDate${achievementCount}" required>
            </div>
            <button type="button" class="btn btn-danger remove-achievement-btn">Remove</button>
        `;
        achievementsContainer.appendChild(newAchievement);
        attachRemoveButtons();
    });

    addEducationButton.addEventListener('click', () => {
        const educationContainer = document.getElementById('educationDetails');
        const educationCount = educationContainer.getElementsByClassName('education-entry').length;
        const newEducation = document.createElement('div');
        newEducation.className = 'education-entry';
        newEducation.innerHTML = `
            <div class="form-group">
                <label for="degree${educationCount}">Degree/Course:</label>
                <input type="text" class="form-control" id="degree${educationCount}" name="degree${educationCount}" required>
            </div>
            <div class="form-group">
                <label for="field${educationCount}">Field of Study:</label>
                <input type="text" class="form-control" id="field${educationCount}" name="field${educationCount}" required>
            </div>
            <div class="form-group">
                <label for="institute${educationCount}">Institute Name:</label>
                <input type="text" class="form-control" id="institute${educationCount}" name="institute${educationCount}" required>
            </div>
            <div class="form-group">
                <label for="marks${educationCount}">Marks/Percentage/GPA:</label>
                <input type="text" class="form-control" id="marks${educationCount}" name="marks${educationCount}" required>
            </div>
            <div class="form-group">
                <label for="startDate${educationCount}">Start Date:</label>
                <input type="date" class="form-control" id="startDate${educationCount}" name="startDate${educationCount}" required>
            </div>
            <div class="form-group">
                <label for="endDate${educationCount}">End Date:</label>
                <input type="date" class="form-control" id="endDate${educationCount}" name="endDate${educationCount}" required>
            </div>
            <button type="button" class="btn btn-danger remove-education-btn">Remove</button>
        `;
        educationContainer.appendChild(newEducation);
        attachRemoveButtons();
    });

    addCertificationButton.addEventListener('click', () => {
        const certificationContainer = document.getElementById('certificationDetails');
        const certificationCount = certificationContainer.getElementsByClassName('certification-entry').length;
        const newCertification = document.createElement('div');
        newCertification.className = 'certification-entry';
        newCertification.innerHTML = `
            <div class="form-group">
                <label for="certificationName${certificationCount}">Certification Title:</label>
                <input type="text" class="form-control" id="certificationName${certificationCount}" name="certificationName${certificationCount}" required>
            </div>
            <div class="form-group">
                <label for="issuingOrganization${certificationCount}">Issuing Organization:</label>
                <input type="text" class="form-control" id="issuingOrganization${certificationCount}" name="issuingOrganization${certificationCount}" required>
            </div>
            <div class="form-group">
                <label for="issueDate${certificationCount}">Date of Issue:</label>
                <input type="date" class="form-control" id="issueDate${certificationCount}" name="issueDate${certificationCount}" required>
            </div>
            <button type="button" class="btn btn-danger remove-certification-btn">Remove</button>
        `;
        certificationContainer.appendChild(newCertification);
        attachRemoveButtons();
    });

    addLanguageButton.addEventListener('click', () => {
        const languageContainer = document.getElementById('languageCompetencies');
        const languageCount = languageContainer.getElementsByClassName('language-entry').length;
        const newLanguage = document.createElement('div');
        newLanguage.className = 'language-entry';
        newLanguage.innerHTML = `
            <div class="form-group">
                <label for="language${languageCount}">Language:</label>
                <input type="text" class="form-control" id="language${languageCount}" name="language${languageCount}" required>
            </div>
            <div class="form-group">
                <label for="proficiency${languageCount}">Proficiency:</label>
                <input type="text" class="form-control" id="proficiency${languageCount}" name="proficiency${languageCount}" required>
            </div>
            <button type="button" class="btn btn-danger remove-language-btn">Remove</button>
        `;
        languageContainer.appendChild(newLanguage);
        attachRemoveButtons();
    });

    function attachRemoveButtons() {
    document.querySelectorAll('.remove-experience-btn').forEach(btn => {
    btn.addEventListener('click', () => btn.parentElement.remove());
    });
    document.querySelectorAll('.remove-project-btn').forEach(btn => {
    btn.addEventListener('click', () => btn.parentElement.remove());
    });
    document.querySelectorAll('.remove-achievement-btn').forEach(btn => {
    btn.addEventListener('click', () => btn.parentElement.remove());
    });
    document.querySelectorAll('.remove-education-btn').forEach(btn => {
        btn.addEventListener('click', () => btn.parentElement.remove());
    });
    document.querySelectorAll('.remove-certification-btn').forEach(btn => {
        btn.addEventListener('click', () => btn.parentElement.remove());
    });
    document.querySelectorAll('.remove-language-btn').forEach(btn => {
        btn.addEventListener('click', () => btn.parentElement.remove());
    });
}

attachRemoveButtons();

    showSection(currentSectionIndex);
    attachRemoveButtons();
});
# Resume Form Application

## Description
This is a simple Flask application that allows users to upload a resume in PDF or DOCX format, processes the uploaded file to extract resume details using Google Generative AI, and fills a form with the extracted data.

## Installation

1. Clone the repository:
    ```bash
    git clone <repository_url>
    ```
2. Change to the project directory:
    ```bash
    cd project
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Run the Flask application:
    ```bash
    python app.py
    ```
2. Open your web browser and go to `http://127.0.0.1:5000` to access the form.

## File Structure

- `app.py`: The main Flask application file.
- `resume.json`: The JSON file containing the resume data.
- `templates/`: The directory containing HTML templates.
- `static/`: The directory containing CSS and JavaScript files.

## Features

- Upload a PDF or DOCX resume.
- Process the uploaded resume using Google Generative AI.
- Fill a form with the extracted data.
- Display a loading screen during processing.

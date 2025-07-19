# 🚀 AI Job Application Assistant

Leverage the power of AI agents to parse your resume, analyze a job description, and automatically tailor your application to stand out. This Streamlit application uses a crew of AI agents to provide specific resume advice, generate a tailored resume draft, and write a compelling cover letter.

## ✨ Key Features

- **📄 Automated Resume Parsing**: Upload your resume in PDF or DOCX format, and the tool will extract the text content.
- **🔍 In-depth Job Description Analysis**: Pastes a job description to have an AI agent deconstruct it into key responsibilities, skills, and qualifications.
- **📊 Initial Match Assessment**: Get a quick, high-level analysis of how well your resume matches the job description *before* making changes.
- **📝 Actionable Tailoring Advice**: Receive specific, bullet-pointed suggestions on how to align your resume with the job requirements, including keywords to add and experiences to highlight.
- **✍️ Automated Resume Tailoring**: Generates a full, rewritten draft of your resume based on the tailoring advice.
- **✉️ Persuasive Cover Letter Drafting**: Creates a personalized and professional cover letter that connects your experience directly to the role's needs.
- **🔄 Interactive Section Refinement**: Fine-tune specific sections of your newly tailored resume with custom instructions (e.g., "make this more concise").

---

## 🤖 How It Works

This project uses **CrewAI** to orchestrate a team of specialized AI agents, each with a specific role in the application process:

1.  **Resume Analyzer**: Extracts and structures information from your resume.
2.  **Job Description Deconstructor**: Breaks down the job posting into its core components.
3.  **Initial Match Analyzer**: Provides a quick pre-analysis of the resume-JD fit.
4.  **Strategic Resume Tailoring Advisor**: Compares the resume and job data to provide actionable improvement advice.
5.  **Expert Resume Editor**: Rewrites the resume based on the advisor's suggestions.
6.  **Persuasive Cover Letter Drafter**: Writes a compelling cover letter using all the analyzed context.
7.  **Resume Section Refinement Specialist**: Makes targeted edits to resume sections based on user feedback.

These agents work sequentially, passing information to one another to build a comprehensive and tailored application package.

---

## 🛠️ Tech Stack

- **Backend**: Python
- **AI Framework**: [CrewAI]
- **LLM Integration**: [LiteLLM] (configured for Google Gemini)
- **Web Framework**: [Streamlit]
- **Data Validation**: [Pydantic]
- **File Parsing**: `PyPDF`, `python-docx`

---

## ⚙️ Setup & Installation

Follow these steps to get the application running on your local machine.

### 1. Prerequisites

- Python 3.8+
- A Google Gemini API Key.

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/AI_JobApplicationAssistant-main.git
cd AI_JobApplicationAssistant-main
```

### 3. Install Dependencies

It's recommended to use a virtual environment.

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install the required packages
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a file named `.env` in the root directory of the project and add your Gemini API key:

```env
GEMINI_API_KEY="your_google_gemini_api_key_here"

# Optional: Specify a Gemini model. Defaults to gemini-1.5-flash-latest if not set.
# GEMINI_MODEL_NAME="gemini-pro"
```

---

## ▶️ How to Run

Once the setup is complete, run the Streamlit application with the following command:

```bash
streamlit run app.py
```

The application will open in a new tab in your web browser.

1.  Upload your resume (PDF or DOCX).
2.  Paste the full job description into the text area.
3.  Click the "✨ Get Application Assistance" button.
4.  Wait for the AI crew to work their magic. The results will be displayed on the page.

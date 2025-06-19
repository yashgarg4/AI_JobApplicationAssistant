try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass
import streamlit as st
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
import os
import tempfile # To handle uploaded files
import litellm
from job_app_tools import ResumeParserTool # Import your custom tool
from models import ResumeDetails, JobDescriptionDetails # Import Pydantic models

# --- Streamlit UI Configuration ---
# Must be the first Streamlit command
st.set_page_config(page_title="AI Job Application Assistant", layout="wide")

# --- LLM Configuration ---
load_dotenv()

# Configure your preferred LLM (e.g., Gemini or OpenAI)
# Example for Gemini:
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    TARGET_LLM_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest")
    litellm.register_model({
        "gemini/" + TARGET_LLM_MODEL: {
            "model_name": TARGET_LLM_MODEL,
            "litellm_provider": "gemini",
            "api_key": GEMINI_API_KEY,
        }
    })
    agent_llm_identifier = f"gemini/{TARGET_LLM_MODEL}"

# st.info(f"Using LLM: {agent_llm_identifier}")

# --- Initialize Tools ---
resume_parser_tool = ResumeParserTool()

# --- Define Agents ---
resume_analyzer_agent = Agent(
    role='Resume Analyzer',
    goal='Extract and understand the key skills, experiences (including roles, responsibilities, achievements), education, and qualifications from the provided resume text.',
    backstory='An expert HR professional skilled in quickly identifying candidate strengths and qualifications from diverse resume formats.',
    llm=agent_llm_identifier,
    verbose=True,
    allow_delegation=False
)

job_description_analyzer_agent = Agent(
    role='Job Description Deconstructor',
    goal='Thoroughly analyze the provided job description to identify key requirements, essential skills (technical and soft), desired qualifications, company culture hints, and the core responsibilities of the role.',
    backstory='A meticulous analyst specializing in deconstructing job postings to pinpoint exactly what employers are seeking in an ideal candidate.',
    llm=agent_llm_identifier,
    verbose=True,
    allow_delegation=False
)

resume_tailoring_advisor_agent = Agent(
    role='Strategic Resume Tailoring Advisor',
    goal='Compare the candidate\'s analyzed resume against the analyzed job description. Provide specific, actionable advice on how to tailor the resume to best match the job requirements. This includes suggesting keywords, highlighting relevant experiences, and bridging any apparent gaps.',
    backstory='A seasoned career coach with a strong track record of helping job seekers optimize their resumes to stand out by perfectly aligning them with specific job opportunities.',
    llm=agent_llm_identifier,
    verbose=True,
    allow_delegation=False
)

cover_letter_drafter_agent = Agent(
    role='Persuasive Cover Letter Drafter',
    goal='Draft a compelling and personalized cover letter. The letter must highlight the candidate\'s most relevant skills and experiences (from their resume analysis) and directly address the requirements outlined in the job description analysis. The tone should be professional, enthusiastic, and tailored to the specific company and role.',
    backstory='A skilled writer and communication expert specializing in crafting persuasive cover letters that capture attention and make candidates memorable.',
    llm=agent_llm_identifier,
    verbose=True,
    allow_delegation=False
)

resume_editor_agent = Agent(
    role='Expert Resume Editor',
    goal='Rewrite and reformat the provided resume text based on specific tailoring advice to perfectly align it with a given job description. The output should be the full text of the revised resume.',
    backstory='A meticulous resume writer with a talent for transforming standard resumes into compelling, job-specific documents that highlight a candidate\'s strengths and experiences in the context of a particular role.',
    llm=agent_llm_identifier,
    verbose=True,
    allow_delegation=False
)

initial_match_analyzer_agent = Agent(
    role='Initial Resume-JD Match Analyzer',
    goal="Provide a quick, high-level assessment of how well a candidate's resume (ResumeDetails JSON) matches a job description (JobDescriptionDetails JSON). Output a qualitative match level (e.g., Strong, Moderate, Needs Improvement) and 2-3 key points highlighting strengths or gaps.",
    backstory="An efficient HR screener adept at quickly identifying the initial fit between a resume and a job posting based on structured data.",
    llm=agent_llm_identifier,
    verbose=True,
    allow_delegation=False
)

section_refiner_agent = Agent(
    role='Resume Section Refinement Specialist',
    goal="Rewrite a specific section of a resume based on a user's explicit instruction to improve its impact, clarity, or focus. The output should be only the refined text for that section.",
    backstory="A detail-oriented editor skilled at making targeted improvements to resume content, ensuring each part is as effective as possible.",
    llm=agent_llm_identifier,
    verbose=True,
    allow_delegation=False
)

# --- Initialize Session State ---
if "advice_output_display" not in st.session_state:
    st.session_state.advice_output_display = ""
if "tailored_resume_output" not in st.session_state:
    st.session_state.tailored_resume_output = ""
if "cover_letter_output" not in st.session_state:
    st.session_state.cover_letter_output = ""
if "initial_match_assessment" not in st.session_state:
    st.session_state.initial_match_assessment = ""
if "section_to_refine" not in st.session_state:
    st.session_state.section_to_refine = ""
if "refinement_instruction" not in st.session_state:
    st.session_state.refinement_instruction = ""
if "refined_section_output" not in st.session_state:
    st.session_state.refined_section_output = ""

# --- Streamlit UI ---
st.title("🚀 AI Job Application Assistant")
st.markdown("Upload your resume and paste a job description to get AI-powered assistance in tailoring your application!")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Your Resume")
    uploaded_resume = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"], key="resume_uploader")

with col2:
    st.subheader("Job Description")
    job_description = st.text_area("Paste the Job Description here", height=350, key="jd_input")

def clear_results():
    st.session_state.advice_output_display = ""
    st.session_state.tailored_resume_output = ""
    st.session_state.cover_letter_output = ""
    st.session_state.initial_match_assessment = ""
    st.session_state.refined_section_output = "" 

if st.button("✨ Get Application Assistance", use_container_width=True):
    if uploaded_resume is not None and job_description.strip():
        # Clear previous results before starting a new run
        clear_results()
        with st.status("🚀 Kicking off the AI job assistant...", expanded=True) as status_ui:
            # Save uploaded file temporarily to pass its path to the tool
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_resume.name)[1]) as tmp_file:
                tmp_file.write(uploaded_resume.getvalue())
                resume_file_path = tmp_file.name
            
            resume_text_content = "" # To store parsed resume text
            try:
                status_ui.update(label="📄 Parsing resume...", state="running")
                # Parse resume using the tool
                st.write(f"Attempting to parse resume from: {resume_file_path}")
                resume_text_content = resume_parser_tool.run(file_path=resume_file_path)

                if "Error:" in resume_text_content:
                    st.error(f"Resume Parsing Failed: {resume_text_content}")
                    st.stop()
                
                st.success("Resume parsed successfully!")
                status_ui.update(label="🔍 Analyzing resume and job description...", state="running")

                # Define Tasks
                task_analyze_resume = Task(
                    description=f"Analyze the following resume text. Extract key information such as work experience (roles, companies, dates, responsibilities, achievements), skills (technical and soft), education (degree, institution, graduation date), and any projects or certifications. Present this as a structured summary.\n\nResume Text:\n```\n{resume_text_content}\n```",
                    expected_output="A JSON object conforming to the ResumeDetails Pydantic model. Ensure all fields are accurately populated based on the resume content. For work experiences, list each role with company, duration, and key achievements/responsibilities as a list of strings.",
                    agent=resume_analyzer_agent,
                    output_pydantic=ResumeDetails
                )

                task_analyze_job_description = Task(
                    description=f"Analyze the following job description. Identify and list the key requirements, essential technical skills, desired soft skills, educational qualifications, years of experience needed, company values or culture hints (if mentioned), and the main responsibilities of the role.\n\nJob Description:\n```\n{job_description}\n```",
                    expected_output="A JSON object conforming to the JobDescriptionDetails Pydantic model. Populate all fields based on the provided job description, ensuring lists are used where appropriate (e.g., for skills, responsibilities).",
                    agent=job_description_analyzer_agent,
                    output_pydantic=JobDescriptionDetails
                )

                task_initial_match_analysis = Task(
                    description="Based on the structured ResumeDetails (JSON) and JobDescriptionDetails (JSON) from the previous tasks, provide a brief, high-level analysis of the initial match. State a qualitative match level (e.g., 'Strong Match', 'Moderate Match', 'Needs Significant Tailoring') and list 2-3 bullet points identifying key strengths or major gaps. Keep the assessment concise.",
                    expected_output="A short paragraph stating the match level, followed by 2-3 bullet points. For example: 'Initial Assessment: Moderate Match. \n- Strength: Relevant experience in X. \n- Gap: Missing explicit mention of Y skill required by JD.'",
                    agent=initial_match_analyzer_agent,
                    context=[task_analyze_resume, task_analyze_job_description]
                )

                task_tailor_resume_advice = Task(
                    description=f"You will receive structured information: the candidate's resume details (as a JSON object conforming to ResumeDetails model) and the job description details (as a JSON object conforming to JobDescriptionDetails model) from previous analysis tasks. Your task is to compare these two. Based on this comparison, provide specific, actionable advice on how to tailor the resume to best match the job requirements. Your advice should be a list of bullet points covering: \n1. Keywords from the JobDescriptionDetails (e.g., from 'must_have_skills', 'key_responsibilities') that should be incorporated into the resume. \n2. Specific skills and experiences from the ResumeDetails (e.g., from 'work_experiences', 'skills') that should be emphasized or elaborated on to match the JobDescriptionDetails. \n3. Any potential gaps between the ResumeDetails and JobDescriptionDetails and how they might be addressed (e.g., highlighting transferable skills). \n4. Suggestions for rephrasing certain points in the resume for better alignment.",
                    expected_output="A clear, bulleted list of actionable recommendations for tailoring the resume. Each recommendation should be specific and justified by referencing parts of the job description or resume.",
                    agent=resume_tailoring_advisor_agent,
                    context=[task_analyze_resume, task_analyze_job_description]
                )

                task_draft_cover_letter = Task(
                    description="Using the analyzed resume, the analyzed job description, and the resume tailoring advice (all from context), draft a professional and engaging cover letter. The letter should: \n1. Clearly state the position being applied for. \n2. Briefly introduce the candidate. \n3. Highlight 2-3 key qualifications and experiences from the resume that directly align with the most important requirements of the job description. \n4. Express enthusiasm for the role and the company. \n5. End with a clear call to action. \nEnsure the tone is professional and tailored.",
                    expected_output="A complete, well-structured draft of a cover letter. It should include a salutation, an introduction, body paragraphs (2-3) demonstrating suitability by referencing specific details from the contextual ResumeDetails (JSON) and JobDescriptionDetails (JSON), and a professional closing. The letter should be ready to be slightly edited and sent by the user.",
                    agent=cover_letter_drafter_agent,
                    context=[task_analyze_resume, task_analyze_job_description, task_tailor_resume_advice]
                )

                task_edit_resume = Task(
                    description="You are provided with the original resume text, the analysis of the job description, and specific tailoring advice. Your goal is to rewrite the *original* resume text by carefully integrating *all* the specific suggestions from the tailoring advice. Maintain the overall structure and sections of the original resume (e.g., Contact Information, Summary/Objective, Experience, Education, Skills). For each work experience entry, revise the bullet points to incorporate keywords and highlight achievements relevant to the job description, as suggested by the tailoring advice. Ensure consistent formatting using clear headings and bullet points (using '*' or '-'). The final output must be the complete, tailored resume text, professionally formatted, in plain text, ready for copy-pasting, with no markdown syntax.",
                    expected_output="The complete, tailored resume text in PLAIN TEXT format. It should be a revised version of the original resume, incorporating the tailoring advice, maintaining a standard resume structure with clear sections and bullet points, and containing NO MARKDOWN formatting whatsoever.",
                    agent=resume_editor_agent,
                    context=[task_analyze_resume, task_analyze_job_description, task_tailor_resume_advice]
                )

                # Create and Run the Crew
                job_application_crew = Crew(
                    agents=[resume_analyzer_agent, job_description_analyzer_agent, initial_match_analyzer_agent, resume_tailoring_advisor_agent, resume_editor_agent, cover_letter_drafter_agent],
                    tasks=[task_analyze_resume, task_analyze_job_description, task_initial_match_analysis, task_tailor_resume_advice, task_edit_resume, task_draft_cover_letter],
                    process=Process.sequential,
                    verbose=True 
                )

                status_ui.update(label="🤖 AI crew is processing... (This may take a few moments)", state="running")
                crew_result = job_application_crew.kickoff()

                # Store results in session state
                st.session_state.initial_match_assessment = str(task_initial_match_analysis.output) if task_initial_match_analysis.output else ""
                status_ui.update(label="💡 Generating tailoring advice...", state="running")
                st.session_state.advice_output_display = str(task_tailor_resume_advice.output) if task_tailor_resume_advice.output else ""
                st.session_state.tailored_resume_output = str(task_edit_resume.output) if task_edit_resume.output else ""
                st.session_state.cover_letter_output = str(crew_result) if crew_result else ""

            except Exception as e:
                st.error(f"An error occurred during the AI processing: {e}")
                import traceback
                status_ui.update(label="❗ Error during processing.", state="error", expanded=False)
                st.error(traceback.format_exc())
            finally:
                # Clean up the temporary file
                if 'resume_file_path' in locals() and os.path.exists(resume_file_path):
                    try:
                        os.remove(resume_file_path)
                        st.write(f"Temporary file {resume_file_path} removed.")
                    except Exception as e_rm:
                        st.warning(f"Could not remove temporary file {resume_file_path}: {e_rm}")
            status_ui.update(label="✅ All tasks complete!", state="complete", expanded=False)
    elif not uploaded_resume and not job_description.strip() and (st.session_state.get("tailored_resume_output") or st.session_state.get("cover_letter_output")):
        # This case is to prevent warning if only download button is clicked on a page with existing results
        pass
    else:
        # Only show this warning if no files are uploaded AND there's no existing session data to display
        if not st.session_state.get("tailored_resume_output") and not st.session_state.get("cover_letter_output"):
            st.warning("⚠️ Please upload your resume and paste the job description to proceed.")

if st.session_state.get("advice_output_display") or st.session_state.get("tailored_resume_output") or st.session_state.get("cover_letter_output") or st.session_state.get("initial_match_assessment"):
    st.button("🧹 Clear Results", on_click=clear_results, use_container_width=True, key="clear_button")

# Display results from session state if they exist
# This block will run on every script execution, including after button clicks.
if st.session_state.get("initial_match_assessment"):
    st.markdown("---")
    st.subheader("🔍 Initial Resume vs. JD Assessment:")
    st.markdown(st.session_state.initial_match_assessment)

if st.session_state.get("advice_output_display"): 
    st.markdown("---")
    st.subheader("📝 Resume Tailoring Advice:")
    st.markdown(st.session_state.advice_output_display)

if st.session_state.get("tailored_resume_output"):
    st.markdown("---")
    st.subheader("📄 Tailored Resume Draft:")
    st.text_area("Tailored Resume:", value=st.session_state.tailored_resume_output, height=400, key="tailored_resume_output_area_persist")
    if st.session_state.tailored_resume_output: 
        st.download_button(
            label="📥 Download Tailored Resume",
            data=st.session_state.tailored_resume_output,
            file_name="tailored_resume.txt",
            mime="text/plain",
            key="download_resume_persist"
        )

if st.session_state.get("cover_letter_output"):
    st.markdown("---")
    st.subheader("✉️ Draft Cover Letter:")
    st.markdown(st.session_state.cover_letter_output)
    if st.session_state.cover_letter_output: 
        st.download_button(
            label="📥 Download Cover Letter",
            data=st.session_state.cover_letter_output,
            file_name="cover_letter.txt",
            mime="text/plain",
            key="download_cover_letter_persist"
        )

# --- Section for Refining Specific Parts of the Tailored Resume ---
if st.session_state.get("tailored_resume_output"): # Only show if a tailored resume exists
    st.markdown("---")
    st.subheader("✨ Refine a Section of Your Tailored Resume")
    
    st.session_state.section_to_refine = st.text_area(
        "Paste the section from your tailored resume you want to refine:",
        value=st.session_state.section_to_refine,
        height=150,
        key="section_to_refine_input"
    )
    st.session_state.refinement_instruction = st.text_input(
        "How should this section be refined? (e.g., 'Make it more concise', 'Add more action verbs', 'Emphasize results')",
        value=st.session_state.refinement_instruction,
        key="refinement_instruction_input"
    )

    if st.button("✍️ Refine Section", key="refine_section_button"):
        if st.session_state.section_to_refine.strip() and st.session_state.refinement_instruction.strip():
            with st.spinner("AI is refining the section..."):
                task_refine_specific_section = Task(
                    description=f"The user has provided the following resume section:\n```\n{st.session_state.section_to_refine}\n```\nAnd wants it refined with this instruction: '{st.session_state.refinement_instruction}'.\nRewrite the provided resume section based *only* on this instruction. Output *only* the refined section text.",
                    expected_output="The refined text of the resume section, directly addressing the user's instruction. Output only the modified section, not any surrounding text or explanation.",
                    agent=section_refiner_agent
                )
                
                # For a single task, create a temporary crew to execute it
                try:
                    refinement_crew = Crew(
                        agents=[section_refiner_agent],
                        tasks=[task_refine_specific_section],
                        verbose=False # less verbose for a single section refinement
                    )
                    refined_text = refinement_crew.kickoff()
                    st.session_state.refined_section_output = str(refined_text) if refined_text else "Could not refine the section."
                except Exception as e:
                    st.error(f"Error during section refinement: {e}")
                    st.session_state.refined_section_output = "Error during refinement."
        else:
            st.warning("Please paste the section to refine and provide a refinement instruction.")

    if st.session_state.get("refined_section_output"):
        st.markdown("---")
        st.subheader("🔍 Refined Section:")
        st.text_area("Refined text (copy and manually update your resume):", value=st.session_state.refined_section_output, height=150, key="refined_section_display")
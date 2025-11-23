from agents import analyze_resume_from_files, create_hr_agent

# Example usage flow:

# Step 1: Analyze resume and job description
print("Step 1: Analyzing resume against job description...")
resume_analysis = analyze_resume_from_files(
    resume_file_path="path/to/resume.pdf",
    job_description_file_path="path/to/job_description.txt"
)

print(f"Match: {resume_analysis['match_percentage']}%")
print(f"Level: {resume_analysis['position_level']}")
print(f"Email: {resume_analysis['email']}")

# Step 2: Create HR conversational agent
print("\nStep 2: Creating HR conversational agent...")
job_description_text = "Full job description text here..."  # Load from file
candidate_email = resume_analysis['email']
hr_name = "John Doe"  # HR person's name

hr_agent = create_hr_agent(
    resume_data=resume_analysis,
    job_description_text=job_description_text,
    candidate_email=candidate_email,
    hr_name=hr_name
)

# Step 3: Ask questions about the candidate
print("\nStep 3: Asking questions...")
response1 = hr_agent.chat("How much experience does this candidate have?")
print(f"Q: How much experience does this candidate have?")
print(f"A: {response1}\n")

response2 = hr_agent.chat("What are their key strengths?")
print(f"Q: What are their key strengths?")
print(f"A: {response2}\n")

response3 = hr_agent.chat("Is this candidate suitable for a senior position?")
print(f"Q: Is this candidate suitable for a senior position?")
print(f"A: {response3}\n")

# Step 4: Generate an email
print("\nStep 4: Generating email...")
email_response = hr_agent.chat(
    "Prepare an email inviting the candidate for an interview. "
    "Subject: Interview Invitation - Software Engineer Position"
)
print(email_response)

# Step 5: Send the email
print("\nStep 5: Sending email...")
send_response = hr_agent.chat("send email")
print(send_response)

# Interactive mode example:
print("\n" + "="*50)
print("Interactive Mode - You can now chat with the agent:")
print("Type 'exit' to quit")
print("="*50)

while True:
    user_input = input("\nHR: ")
    if user_input.lower() in ['exit', 'quit', 'q']:
        break
    
    response = hr_agent.chat(user_input)
    print(f"\nAgent: {response}")


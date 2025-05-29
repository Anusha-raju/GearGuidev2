import os
from dotenv import load_dotenv
import PyPDF2
import openai

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('MODEL')


def extract_pdf_content(pdf_path):
    content = []
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            content.append(page.extract_text())
    return "\n".join(content)


def structure_content_with_llm(text):
    all_structured_data = []
    try:
        max_chunk_size = 5000
        chunks = [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]

        # Process each chunk individually
        for chunk in chunks:
            # prompt for each chunk
            prompt = f"""
            You are a car mechanic guide. Extract and structure the following information into suitable categories such as:
            - Problem
            - Symptom
            - Suspect Area
            - Information on Suspect Area
            - Tests and Procedure (if applicable)

            If these categories aren't suitable, label the information with appropriate titles from the information itself. 
            Wrap each category and its information in XML-like tags. Here’s the information you need to process:

            {chunk}

            Example Output (in XML format):
            <problem>...</problem>
            <symptom>...</symptom>
            <suspect_area>...</suspect_area>
            <suspect_area_info>...</suspect_area_info>
            <test>
                <name>...</name>
                <procedure>...</procedure>
            </test>
            <additional info>...</additional info>

            the tag names should match the category or label. Also place any additional info or non classified information into additional info tag.
            Also extract the details of the car such as model number, type, manufacturer etc.., if available with suitable tags else do not include these tags.
            """

            response = openai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )

            # print(response)
            structured_output = response.choices[0].message.content

            if structured_output.strip():
                all_structured_data.append(structured_output.strip())

    except:
        pass
    finally:
        return "\n".join(all_structured_data)
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate
import re
import zipfile
import os


def get_text_from_pdf(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        first_page_text = pdf_reader.pages[0].extract_text()
        if "Software Requirements Specification" in first_page_text or "SRS" in first_page_text:
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            st.error("Please upload a Software Requirements Specification(SRC) file")
            return None
    return text


def get_text_from_txt(txt_docs):
    text = ""
    for txt in txt_docs:
        text += txt.getvalue().decode('utf-8') + "\n"

        # Check if the TXT contains the required heading
        if "Software Requirements Specification" not in text and "SRS" not in text:
            st.error("Please upload a Software Requirements Specification(SRC) file")
            return None
    return text


def get_text_content(uploaded_files):
    text = ""
    for file in uploaded_files:
        if file.type == 'application/pdf':
            text += get_text_from_pdf([file]) or ""
    
        elif file.type == 'text/plain':
            text += get_text_from_txt([file]) or ""
        else:
            st.error(f"File format '{file.type}' is not supported. Please upload a PDF, DOCX, or TXT file.")
            return None
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore


def get_conversation_chain(vectorstore):
    selected_num_test_cases = st.radio("Select the number of test cases to generate:", [1, 2, 3, 4, 5])
    general_system_template = r"""
    {context}
    {question}
Please select the number of test cases you want to generate:
{num_test_cases}. Generate {num_test_cases} test cases.
Generate {num_test_cases} test cases in proper format with their codes based on a user's input user story and the associated Software Requirements Specification (SRS) file. Your goal is to ensure that all possible test scenarios are covered.
Please follow the format below when generating test cases:

Example User Story:
As an online shopper, I want to be able to add products to my shopping cart, review the cart, and proceed to checkout to make a purchase.

Acceptance Criteria:
The e-commerce website is accessible.
The website displays a catalog of products.
Users can select products to add to their shopping cart.
Users can view the contents of their shopping cart.
Users can proceed to the checkout process to complete a purchase.

Example Test Case:

Test Case 1: Adding a Product to the Cart

ID: TC-ECOM-001

Priority: High

Preconditions:
The e-commerce website is accessible.
There are products available in the catalog.

Test Steps:
1. Open the web browser.
2. Navigate to the e-commerce website.
3. Browse the product catalog and select a product.
4. Click the "Add to Cart" or "Buy Now" button for the selected product.

Expected Result:
- The selected product should be added to the shopping cart.
- The user should see a confirmation message indicating that the product has been added.

Postconditions:
The selected product is added to the user's shopping cart.

Test Data:
User is logged in as: user@example.com

Test Environment:
- Web browser (latest version)
- E-commerce website product catalog page

Test Execution:
- Execute the test steps as described.
- Verify that the selected product is added to the shopping cart.
- Check that the user sees a confirmation message indicating successful addition.

Pass Criteria:
- The product is successfully added to the shopping cart.
- The user receives a confirmation message.

Fail Criteria:
- The product is not added to the shopping cart.
- An error message is displayed indicating the addition was unsuccessful.

Now, using the provided user story and any relevant information from the attached SRS file, your task is to generate all possible test cases in the format described above. Ensure that each test case is clear, specific, and covers various scenarios related to the user story. And generate the selenium code (python) for the test steps of the each possible test cases with the heading Selenium Code (Python).
Use options keyword argument to run Chrome in headless mode. Automatically determine the path to the WebDriver executable and support multiple browsers (chrome, firefox, and microsoft edge) using the webdriver_manager package in Python.
"""
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(),
        retriever=vectorstore.as_retriever(),
        memory=memory,
        chain_type="stuff",
    )
    QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"], template=general_system_template.replace("{num_test_cases}", str(selected_num_test_cases))
)
    conversation_chain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=QA_CHAIN_PROMPT)
    return conversation_chain


def zip_test_cases(all_test_cases):
    with zipfile.ZipFile('test_cases.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for test_case_number, test_case in all_test_cases:
            file_name = f'test_case_code_{test_case_number}.py'
            # Create a test case description file with the test case number heading
            test_case_description = f'Test Case {test_case_number} description.txt'
            with open(test_case_description, 'w') as desc_file:
                desc_file.write(f'Test Case {test_case_number}:\n\n{test_case}')
            # Add the description file to the zip
            zipf.write(test_case_description, f'Test Case {test_case_number}/{test_case_description}')
            # Add the code file to the zip
            zipf.write(file_name, f'Test Case {test_case_number}/{file_name}')


def handle_userinput(user_question):
    if st.session_state.conversation is not None:
        with st.spinner("Generating Response..."):  
            response = st.session_state.conversation({'question': user_question})
            pattern = r'Test Case (\d+):([^`]+)Selenium Code \(Python\):\n```python\n(.*?)```'
            matches = re.findall(pattern, response['answer'], re.DOTALL)
            all_test_cases = []

            for idx, match in enumerate(matches):
                test_case_number = match[0].strip()
                test_case = match[1].strip()
                test_case_code = match[2].strip()
                file_name = f'test_case_code_{test_case_number}.py'
                with open(file_name, 'w') as file:
                    file.write(test_case_code)
              
                all_test_cases.append((test_case_number, test_case))

            # Display the test cases with formatted titles (bold)
            st.write("Generated Test Cases:")
            for test_case_number, test_case in all_test_cases:
                formatted_test_case = user_template.replace("{{MSG}}",f'<b style="font-size: 20px;">Test Case {test_case_number}:</b> \n\n{test_case}\n')
                st.write(formatted_test_case, unsafe_allow_html=True)
                try:
                    exec(open(file_name).read())
                except Exception as e:
                    st.error(f"Error executing saved Selenium code: {str(e)}")

            # Create a download button for all the test cases with formatted headings
            all_test_cases_text = "\n\n".join([f'User Story:\n\n{user_question}\n\nTest Case {test_case_number}: {test_case}\n' for test_case_number, test_case in all_test_cases])
            
            # Zip the test cases and code files
            zip_test_cases(all_test_cases)
            
            # Provide a button to initiate the download of the zip file
            if st.button("Download All Test Cases"):
                st.write("Initiating download...")
                st.download_button(
                    label="Download All Test Cases",
                    data=open('test_cases.zip', 'rb').read(),
                    file_name="test_cases.zip",
                    mime="application/zip",
                )

            # Clean up the test case description files after zipping
            for test_case_number, _ in all_test_cases:
                test_case_description = f'Test Case {test_case_number} description.txt'
                if os.path.exists(test_case_description):
                    os.remove(test_case_description)
    else:
        st.error("Please upload an SRS document.")

        
def main():
    load_dotenv()
    custom_css = """
<style>
.center-align {
    text-align: center;
}
</style>
"""
    st.set_page_config(page_title="Test Cases Generation",
                       page_icon=":magic_wand:")
    st.write(css, unsafe_allow_html=True)
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    st.markdown(custom_css, unsafe_allow_html=True)
    st.header("Story2Test: Streamlining User Story to Test Case Conversion")
    uploaded_files = st.file_uploader("Upload your SRS document:", accept_multiple_files=True)

    if uploaded_files:
        with st.spinner("Processing"):
            for uploaded_file in uploaded_files:
                text = get_text_content([uploaded_file])
                if text:
                    text_chunks = get_text_chunks(text)
                    vectorstore = get_vectorstore(text_chunks)
                    st.session_state.conversation = get_conversation_chain(
                            vectorstore)
    with st.form(key='user_input_form'):
        user_question = st.text_area("Enter a user story according to your SRS:")
        generate_button = st.form_submit_button("Generate Test Cases")
    if generate_button:
        if user_question:
            handle_userinput(user_question)
            
        
if __name__ == '__main__':
    main()

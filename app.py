import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        # Check if the PDF contains the required heading
        first_page_text = pdf_reader.pages[0].extract_text()
        if "Software Requirements Specification" in first_page_text or "SRS" in first_page_text:
            for page in pdf_reader.pages:
                text += page.extract_text()
        else:
            st.error("Please upload a Software Requirements Specification(SRC) file")
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
    general_system_template = r""" 
    
    {context}
    {question}   

    You are a chatbot who is responsible to generate all the possible test cases of the user story given by the user.
    Make sure that you cover all the possible test cases.
    ----

    Example User Story:
    As an online shopper, I want to be able to add products to my shopping cart, review the cart, and proceed to checkout to make a purchase.

    Acceptance Criteria:
    The e-commerce website is accessible.
    The website displays a catalog of products.
    Users can select products to add to their shopping cart.
    Users can view the contents of their shopping cart.
    Users can proceed to the checkout process to complete a purchase.
    
    Example Test case:
    
    Test Case 1: Adding a Product to the Cart

    Title: User adds a product to the shopping cart
    
    ID: TC-ECOM-001
    
    Priority: High
    
    Preconditions:
    The e-commerce website is accessible.
    There are products available in the catalog.
    
    Test Steps:
    Open the web browser.
    Navigate to the e-commerce website.
    Browse the product catalog and select a product.
    Click the "Add to Cart" or "Buy Now" button for the selected product.
    
    Expected Result:
    The selected product should be added to the shopping cart.
    The user should see a confirmation message indicating that the product has been added.
    
    Postconditions:
    The selected product is added to the user's shopping cart.
    
    Test Data:
    User is logged in as: user@example.com
    
    Test Environment:
    Web browser (latest version)
    E-commerce website product catalog page
    
    Test Execution:
    Execute the test steps as described.
    Verify that the selected product is added to the shopping cart.
    Check that the user sees a confirmation message indicating successful addition.
    
    Pass Criteria:
    The product is successfully added to the shopping cart.
    The user receives a confirmation message.
    
    Fail Criteria:
    The product is not added to the shopping cart.
    An error message is displayed indicating the addition was unsuccessful.
    
    I provided an example of a user story and test case above. Now your job is to generate all the possible test cases with the same format as given above
    of the user story given by user.
"""

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(),
        retriever=vectorstore.as_retriever(),
        memory=memory,
        chain_type="stuff",
    )
    QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],template=general_system_template)

    conversation_chain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=QA_CHAIN_PROMPT)

    return conversation_chain

def handle_userinput(user_question):
    if st.session_state.conversation is not None:
        response = st.session_state.conversation({'question': user_question})
        st.session_state.chat_history = response['chat_history']

        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(user_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
    else:
        st.error("Please upload an SRS document.")



def main():
    load_dotenv()
    st.set_page_config(page_title="Test Cases Generation",
                       page_icon=":magic_wand:")
    st.markdown("""
    <style>
    .centered-button {
        text-align: center;
    }
    </style>""", unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Story2Test: Streamlining User Story to Test Case Conversion:")
    
    # Create a form with the input field and button
    with st.form(key='user_input_form'):
        user_question = st.text_input("Enter a user story according to your SRS:")
        generate_button = st.form_submit_button("Generate Response")

    # Check if the button is clicked and then generate the response
    if generate_button:
        if user_question:
            handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your SRS document")
        pdf_docs = st.file_uploader(
            "Upload your SRS document here", accept_multiple_files=True)
        
        if pdf_docs:
            for pdf in pdf_docs:
                # Check if the uploaded file is a PDF
                if pdf.type != 'application/pdf':
                    st.error("File type is not valid. Please upload a PDF file.")
                    return

                with st.spinner("Processing"):
                    raw_text = get_pdf_text(pdf_docs)
                    if raw_text is not None:
                        text_chunks = get_text_chunks(raw_text)
                        vectorstore = get_vectorstore(text_chunks)
                        st.session_state.conversation = get_conversation_chain(
                            vectorstore)

if __name__ == '__main__':
    main()
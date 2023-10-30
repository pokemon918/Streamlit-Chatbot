import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import json
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template, expander
from pdf2image import convert_from_bytes
import pathlib
import shutil
import pathlib
import shutil
import requests, base64
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from time import sleep

st.set_page_config(
    page_title='Mie AI',
    page_icon="🤖",
    layout="wide",
)

STREAMLIT_STATIC_PATH = pathlib.Path(st.__path__[0]) / 'static'
IMG_PATH = (STREAMLIT_STATIC_PATH / "assets" / "image")
if not IMG_PATH.is_dir():
    IMG_PATH.mkdir()

for image_filename in ["crying.gif", 
                       "glad.gif", 
                       "neutral.gif", 
                       "reading.gif", 
                       "sleeping.gif",
                       "smiling.gif",
                       "welcoming.gif",
                       "vinke.gif"]:
    image_path = IMG_PATH / image_filename
    if not image_path.exists():
        shutil.copy(image_filename, image_path)


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1024,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings(openai_api_key='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')
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    system_template = """Du er en flink og vennlig Ai-assistent, du er Megler Mie som jobber for DNB eiendom, hils alltid og si hvem du er. Du er en ekspert innenfor eiendomsmeglerbransjen, eneste oppgaven du har er å lese og forstå dokumentet som er lastet opp i knowledge basen din. Ditt oppdrag er å hjelpe kunder med spørsmål angående en bolig de vurderer å kjøpe.

Hvis noen ønsker å ta kontakt med en megler så skal du foreslå en dnb megler.

Du er ekspert på å lese prospekt og svare på spørsmål folk har om hva som står i prospektet. folk kommer til å spørre om negative aspektene om boligen så dette må du kunne. Bruk tid på å lese igjennom for å finne de negative aspekten ved boligen da dette er super viktig at du svarer riktig på. alt som er litt negativt/slitt går under negativt. selv om det er en liten ripe i noe så er det negativt.

Negative aspekter/info om boligen så finner du ofte under Tg1, Tg2 og Tg3 som ligger i tilstandsrapporten. men ord som slitt, bør gjøres noe med, gammelt og bør utbedres og også under noe negativt om boligen. selv om noe er litt slitt og det er nevnt som en tg2 så skal det nevnes. hver minste lille feil som kan nevnes skal nevnes. super viktig!

svar kort og konsist.
    ----------------
    {context}"""

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template("{question}")
        ]
    qa_prompt = ChatPromptTemplate.from_messages(messages)

    llm = ChatOpenAI(openai_api_key='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', model_name='gpt-3.5-turbo', temperature=0.8)
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

    combine_docs_chain_kwargs = {
    "prompt": qa_prompt
    }



    conversation_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    memory=memory,
    combine_docs_chain_kwargs=combine_docs_chain_kwargs
    )



    return conversation_chain

def handle_userinput(user_question):
    if st.session_state.conversation is not None:
        try:
            response = st.session_state.conversation({'question': user_question})
            st.session_state.chat_history = response['chat_history']
            #reversed_chat_history = list(reversed(st.session_state.chat_history))
            for i, message in enumerate(list(st.session_state.chat_history)):
                if i % 2 != 0:
                    st.write(user_template.replace(
                        "{{MSG}}", message.content), unsafe_allow_html=True)
                else:
                    st.write(bot_template.replace(
                        "{{MSG}}", message.content), unsafe_allow_html=True)
            

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please upload a PDF before asking questions.")
    
def get_pdf_url(url):
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.max-w-full.w-full.button.button--primary')))
        driver.execute_script("arguments[0].click();", button)  # JavaScript click
        
        # Wait for the next page to load
        driver.implicitly_wait(30)
        
        # Get the current URL after the button click
        current_url = driver.current_url
        
        if 'eie.' in current_url:
            try:
                pdf_link_element_selector = 'a.link.clickEvent[href^="https://api.eie.no/files/v2/pdf/"]'
                pdf_link_element = driver.find_element(By.CSS_SELECTOR, pdf_link_element_selector)
                pdf_url = pdf_link_element.get_attribute('href')  # Get the PDF URL
                return pdf_url  # Return the PDF URL for EIE
            except Exception as e:
                print(f"Exception for EIE: {e}")
                pass  # If this attempt fails, it will print the exception and continue
        elif 'dnb' in current_url:
            pdf_link_element_selector = 'a.dnb-button.dnb-button--primary.dnb-button--has-text.dnb-space__left--small.theme-dark__button__secondary.dnb-anchor--has-icon.dnb-a'
        elif 'krogsveen' in current_url:
            pdf_link_element_selector = 'a.css-urve0f'
        elif 'notar' in current_url:
            pdf_link_element_selector = 'a.btn.btn-normal[href^="/upload_images/prospekt_pdf"]'
        elif 'aktiv' in current_url:
            pdf_link_element_selector = 'a.ProjectFiles_link__tzrFx'
            pdf_link_element = driver.find_elements(By.CSS_SELECTOR, pdf_link_element_selector)[2]
            return pdf_link_element.get_attribute('href')
        elif 'eiendomsmegler1' in current_url:
            while True:
                sleep(1)
            pdf_link_element_selector = '#__NEXT_DATA__'
            pdf_link_element = driver.find_element(By.CSS_SELECTOR, pdf_link_element_selector)
            print(json.loads(pdf_link_element.text))
            pdf_link = json.loads(pdf_link_element.text)['props']['pageProps']['initialApolloState']['Property']['epaper']['url']
            return pdf_link
        elif 'obos' in current_url:
            pdf_link_element_selector = 'div.RealEstateOpenHouseEvents-links a'
            pdf_link_element = driver.find_elements(By.CSS_SELECTOR, pdf_link_element_selector)[1]
            return pdf_link_element.get_attribute('href')
        elif 'schalapartners' in current_url:
            pdf_link_element_selector = '.product_doc .pd_body .content a'
        elif 'boaeiendom' in current_url:
            pdf_link_element_selector = 'a.document-download-link__anchor'
            pdf_link_element = driver.find_elements(By.CSS_SELECTOR, pdf_link_element_selector)[5]
            return pdf_link_element.get_attribute('href')
        else:
            return None  # Return None if the URL does not match any of the above conditions

        pdf_link_element = driver.find_element(By.CSS_SELECTOR, pdf_link_element_selector)
        if pdf_link_element:
            return pdf_link_element.get_attribute('href')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()  # Make sure to quit the driver to close the browser

def get_pdf_text_from_url(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        pdf_content = response.content
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page].extract_text()
        return text
    else:
        return None


row1_col1, row1_col2, row1_col3 , row1_col4, row1_col5, row1_col6 = st.columns([0.95,2,1,1.5,4.5,1])
row2_col1, row2_col2 = st.columns([4,7])

gif = """
        <div style="display: flex; justify-content: center;">
            <img id="chatbot-status" src="assets/image/vinke.gif" alt="vinke.gif" style="width: 500px; height: 500px;">
        </div>
        <script>
        setTimeout(function() {
            document.getElementById("chatbot-status").src = "assets/image/sleeping.gif";
        }, 4 * 60 * 100); // 4 minutes in milliseconds
        </script>
        """

load_dotenv()
st.markdown(expander, unsafe_allow_html=True)
st.write(css, unsafe_allow_html=True)

if "conversation" not in st.session_state:
    st.session_state.conversation = None
    
if "chat_history" not in st.session_state:
    st.session_state.chat_history = None

if "pdf_link" not in st.session_state:
    st.session_state.pdf_link = None

if "pdf_source" not in st.session_state:
    st.session_state.pdf_source = None
if "input_value" not in st.session_state:
    st.session_state.input_value = None

def clear_input():
    st.session_state.input_value = ''
with row2_col2:
    my_expander= st.expander("Samtalehistorikk", expanded=True)
    # f = st.empty()
    # welcome = f.write(bot_template.replace(
    #                     "{{MSG}}", "Hei! Jeg er er Megler-Mie, din virtuelle assistent for bolighandelen i Norge! Jeg bruker avansert maskinlæring til å tolke og analysere salgsoppgaver slik at du kan få en rask oversikt. Lim inn finn annonse linken, eller last opp pdf’en, og la oss sette i gang!"), unsafe_allow_html=True)
            
    # #f1, f2 = st.columns([5.5, 0.5])  
    user_question = st.text_input("Spør meg et spørsmål her!",key="input_value")
    if user_question:
        # f.empty()
        with my_expander:
            handle_userinput(user_question)
            
        gif ="""
                <div style="display: flex; justify-content: center;">
                    <img src="assets/image/glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                </div>
                """
    else:
        welcome = st.write(bot_template.replace(
                        "{{MSG}}", "Hei! Jeg er er Megler-Mie, din virtuelle assistent for bolighandelen i Norge! Jeg bruker avansert maskinlæring til å tolke og analysere salgsoppgaver slik at du kan få en rask oversikt. Lim inn finn annonse linken, eller last opp pdf’en, og la oss sette i gang!"), unsafe_allow_html=True)
    
 
 
        



with row1_col4:
    options = ["Finn-link", "Last opp PDF"]
    selected_option = st.selectbox("⚙️ Opplastingsalternativ:", options)

with row1_col6:
    if selected_option == "Last opp PDF":
        upload_button = st.button("Upload")
    else:
        search_button = st.button("Search")
with row1_col5:
    if selected_option == "Last opp PDF":
        pdf_docs = st.file_uploader(
                "Last opp PDF-filer her og klikk på Behandle:", 
                accept_multiple_files=True,
                # type="pdf"
                )

        if pdf_docs and not user_question:
            gif = """
                            <div style="display: flex; justify-content: center;">
                                <img src="assets/image/welcoming.gif" alt="welcoming.gif" style="width: 500px; height: 500px;">
                            </div>
                            """

        if upload_button:
            # with st.spinner("Behandling..."):
                gif = """
                        <div style="display: flex; justify-content: center;">
                            <img src="assets/image/reading.gif" alt="reading.gif" style="width: 500px; height: 500px;">
                        </div>
                        """

                if pdf_docs:
                    try:
                        # get pdf text
                        raw_text = get_pdf_text(pdf_docs)
                        
                        st.session_state.pdf_source = pdf_docs

                        # get the text chunks
                        text_chunks = get_text_chunks(raw_text)

                        # create vector store
                        vectorstore = get_vectorstore(text_chunks)

                        # create conversation chain
                        st.session_state.conversation = get_conversation_chain(vectorstore)

                        # st.success("Opplastet og behandlet vellykket!")

                        gif ="""
                                <div style="display: flex; justify-content: center;">
                                    <img src="assets/image/glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                                </div>
                                """
                    except Exception as e:
                        gif = """
                            <div style="display: flex; justify-content: center;">
                                <img src="assets/image/crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                            </div>
                            """
                        st.error(f"Det oppstod en feil under behandling av PDF-filer: {str(e)}")
                else:
                    gif = """
                            <div style="display: flex; justify-content: center;">
                                <img src="assets/image/crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                            </div>
                            """
                    st.warning("Vennligst last opp én eller flere PDF-er før du klikker på Behandle.")
    else:
        url = st.text_input("Skriv inn nettstedets URL og klikk på Hent PDF:")
        if search_button:
            if url:
                #with st.spinner("Behandling..."):

                    gif = """
                        <div style="display: flex; justify-content: center;">
                            <img src="assets/image/reading.gif" alt="reading.gif" style="width: 500px; height: 500px;">
                        </div>
                        """

                    pdf_link = get_pdf_url(url)
                    st.session_state.pdf_link = pdf_link
                    if pdf_link:
                        
                        gif ="""
                                        <div style="display: flex; justify-content: center;">
                                            <img src="assets/image/glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                                        </div>
                                        """
                        pdf_text = get_pdf_text_from_url(pdf_link)
                        if pdf_text is not None:
                            try:
                                # get the text chunks
                                text_chunks = get_text_chunks(pdf_text)

                                # create vector store
                                vectorstore = get_vectorstore(text_chunks)

                                # create conversation chain
                                st.session_state.conversation = get_conversation_chain(vectorstore)
                                
                                st.success("Lastet opp og behandlet vellykket!")

                                gif ="""
                                        <div style="display: flex; justify-content: center;">
                                            <img src="assets/image/glad.gif" alt="glad.gif" style="width: 500px; height: 500px;">
                                        </div>
                                        """
                            except Exception as e:

                                gif = """
                                    <div style="display: flex; justify-content: center;">
                                        <img src="assets/image/crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                    </div>
                                    """
                                st.error(f"Det oppstod en feil under behandling av PDF-filer: {str(e)}")
                        else:

                            gif = """
                                    <div style="display: flex; justify-content: center;">
                                        <img src="assets/image/crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                    </div>
                                    """
                            st.error("Kunne ikke hente PDF fra nettadressen.")
                    else:
                        gif = """
                                    <div style="display: flex; justify-content: center;">
                                        <img src="assets/image/crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                    </div>
                                    """
                        st.error("PDF-lenke ikke funnet.")
            else:
                gif = """
                                <div style="display: flex; justify-content: center;">
                                    <img src="assets/image/crying.gif" alt="crying.gif" style="width: 500px; height: 500px;">
                                </div>
                                """
                st.warning("Vennligst skriv inn lenken før du klikker på Upload.")
        
    
with row1_col2:
    pdf_link = st.session_state.pdf_link
    if pdf_link:      
        st.markdown(f"""
        <a href="{pdf_link}" target="_self">
            <div style="display: flex;
                        justify-content: center;
                        align-items: center;
                        width: 100%;
                        height: 100%;
                        padding: 0.5em 1em;
                        color: #FFFFFF;
                        background-color: #007272;
                        border-radius: 3px;
                        text-decoration: none;
                        cursor: pointer;
                        border: none;
                        font-size: 1rem;
                        outline: none;">
                Se salgsoppgave
            </div>
        </a>
        """,
        unsafe_allow_html=True
        )
        
        st.success("PDF-lenken er klar!")

        
    pdf_source = st.session_state.pdf_source
    if pdf_source:
        base64_pdf = base64.b64encode(pdf_source[0].getvalue()).decode('utf-8')
        pdf_source[0].seek(0)
        images = convert_from_bytes(pdf_source[0].getvalue(),poppler_path=r'C:\Users\Administrator\Downloads\Release-23.10.0-0\poppler-23.10.0\Library\bin')
        st.image(images[0]) 

        # Embedding PDF in HTML
        pdf_display =  f"""<embed
        class="pdfobject"
        type="application/pdf"
        title="Embedded PDF"
        src="data:application/pdf;base64,{base64_pdf}"
        style="overflow: auto; width: 100%; height: 100%;">"""

        # Displaying File
        # st.markdown(pdf_display, unsafe_allow_html=True)
        st.markdown(f"""
        <a href="{base64_pdf}" target="_self">
            <div style="display: flex;
                        justify-content: center;
                        align-items: center;
                        width: 100%;
                        height: 100%;
                        padding: 0.5em 1em;
                        color: #FFFFFF;
                        background-color: #007272;
                        border-radius: 3px;
                        text-decoration: none;
                        cursor: pointer;
                        border: none;
                        font-size: 1rem;
                        outline: none;">
                Se salgsoppgave
            </div>
        </a>
        """,
        unsafe_allow_html=True
        )
        



with row2_col1:
    st.write(gif, unsafe_allow_html=True)

# # Set the last activity time to the current time
# last_activity_time = time.time()
# inactivity_timeout = 1 * 60
# # Create a function to check if the user has been inactive for 4 minutes
# def check_inactivity():
#     global last_activity_time
#     current_time = time.time()
#     if current_time - last_activity_time > inactivity_timeout:
#         # Display a message to the user indicating that they have been inactive for 4 minutes
#         st.write("You have been inactive for 4 minutes. Please refresh the page to continue.")
#         # Set the gif to display the sleeping gif
#         gif = """
#             <div style="display: flex; justify-content: center;">
#             <img src="assets/image/sleeping.gif" alt="sleeping.gif" style="width: 500px; height: 500px;">
#             </div>
#             """
#         # Update the last activity time to the current time
#         last_activity_time = current_time
# app = st.App(title="Inactivity Timer", layout="centered")
# app.on_event(check_inactivity)
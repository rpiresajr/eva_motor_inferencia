import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from PyPDF2 import PdfReader
import uuid
from cassandra_db import CassandraDB
from ocr import OCR
from templates import template1, template2, template_saudacao
import json

openai_api_key = st.secrets["OPENAI_API_KEY"]
memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")
memory.save_context({"human_input": "assistant"}, {"output": "Você é um representante comercial querendo vender um produto ou uma franquia. Lembre todas as perguntas que o humano fizer"})

if "sessionUser" not in st.session_state:
    st.session_state.sessionUser = str(uuid.uuid4())

st.set_page_config(
    page_title="E.V.A.",
    page_icon="👋",
)

def send_email():
  pass
    
def main(cass_db, ocr):
  st.title("E.V.A. - Engine for Virtual Attendant")
  with st.sidebar:
    allow_img = st.toggle("Leitura de imagens", value=False)  
    on = st.toggle("Ficar no contexto", value=True)
    if on:
      template = template1
      st.write("Só Contexto")
    else:
      template = template2
      st.write("Contexto + Internet")
      
    with st.form("form_upload", clear_on_submit=True):
      docs = st.file_uploader("Insira seus arquivos", type="pdf", accept_multiple_files=True)
      if(st.form_submit_button("Enviar documentos", type='secondary')):
        for file in docs:
          text = extract_text(file)
          if allow_img:
            text += ocr.extract_from_images(file)
          cass_db.write_vectors_from_text(text, file.name)
          print(f"Uploaded: {file.name}")
        print("Uploaded complete!")
     
    with st.form("form_new_chat", clear_on_submit=True):
      if st.form_submit_button("Novo chat", type='secondary'):
        st.session_state.clear()
        
    with st.expander("Arquivos carregados..."):
      files = cass_db.get_files()
      
      for file in list(files.keys()):
        if st.button("Apagar", key=file):
          cass_db.delete_document(file)
          st.rerun()
        st.markdown(f"{file} [{files[file]}]")
      
  if "sessionId" not in st.session_state:
    st.session_state.sessionId = str(uuid.uuid4())
  
  if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": introduce_yourself(memory)})
  
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])
    memory.save_context({"human_input": message['role']}, {"output": message['content']})

  if prompt := st.chat_input("Digite algo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
      docs = cass_db.get_documents(prompt)
      
      prompt2 = PromptTemplate(input_variables=["chat_history", "human_input", "context"], template=template)
      chain = load_qa_chain(ChatOpenAI(temperature=0.4, model="gpt-4o"), chain_type="stuff", memory=memory, prompt=prompt2)

      query = prompt
      result = chain({"input_documents": docs, "human_input": query}, return_only_outputs=True)

      resp = result['output_text'].replace("R$", "R\$")
      st.markdown(resp)
      st.session_state.messages.append({"role": "assistant", "content": resp})
      cass_db.write_questions_from_text(f"Pergunta: {prompt}\nResposta: {resp}", st.session_state.sessionId)
      print(chain.memory.buffer)
    
def introduce_yourself(memory):
  prompt = PromptTemplate(input_variables=["chat_history", "human_input", "context"], template=template_saudacao)
  chain = load_qa_chain(ChatOpenAI(temperature=0.9, model="gpt-4o"), chain_type="stuff", memory=memory, prompt=prompt)

  query = "Se apresente de maneira informal para o usuário falando sobre é um assistente da JAH e irá ajudá-lo"
  result = chain({"input_documents": [], "human_input": query}, return_only_outputs=True)
  return result['output_text']
  # st.markdown(result['output_text'])
  
def extract_text(pdf):
  text = ""
  pdf_reader = PdfReader(pdf)
  for page in pdf_reader.pages:
      page_text = page.extract_text()
      text += page_text
  return text

if __name__ == '__main__':
  cass = CassandraDB()
  ocr = OCR()
  main(cass, ocr)
  
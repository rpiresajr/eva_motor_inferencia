import streamlit as st
from langchain_openai import OpenAI
from langchain.chains import ConversationChain  
from langchain.memory import ConversationBufferMemory
from PyPDF2 import PdfReader

from cassandra_db import CassandraDB

openai_api_key = st.secrets["OPENAI_API_KEY"]
llm = OpenAI(temperature=0)

def generate_response(input_text):
    llm = OpenAI(temperature=0.7, openai_api_key=openai_api_key)
    st.info(llm(input_text))

            
def main(cass_db):
  conversation = ConversationChain(
      llm=llm,
      verbose=True,
      memory=ConversationBufferMemory()
  )
  st.title("E.V.A.")
  with st.sidebar.form("form_upload"):
    docs = st.file_uploader("Insira seus arquivos", type="pdf", accept_multiple_files=True)
    if(st.form_submit_button("Enviar documentos", type='secondary')):
      for file in docs:
        text = extract_text(file)
        cass_db.write_vectors_from_text(text, file.name)
  
  if "messages" not in st.session_state:
    st.session_state.messages = []
  
  conversation.memory = ConversationBufferMemory()
  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])
    conversation.memory.save_context({"input": message['role']}, {"output": message['content']})

  if prompt := st.chat_input("Digite algo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
      stream = cass_db.search(prompt)
      st.session_state.messages.append({"role": "assistant", "content": stream})
      # conversation.memory.save_context({"input": "assistant"}, {"output": stream})
      conversation.predict(input=prompt)
      resp = conversation.memory.buffer_as_messages[-1].content
      st.write(resp)
    
def extract_text(pdf):
  text = ""
  pdf_reader = PdfReader(pdf)
  for page in pdf_reader.pages:
      page_text = page.extract_text()
      text += page_text
  return text
          
if __name__ == '__main__':
  cass = CassandraDB()
  main(cass)
  
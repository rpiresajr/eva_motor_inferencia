import streamlit as st
from langchain_openai import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

openai_api_key = st.secrets["OPENAI_API_KEY"]
llm = OpenAI(temperature=0)


def generate_response(input_text):
    llm = OpenAI(temperature=0.7, openai_api_key=openai_api_key)
    st.info(llm(input_text))

            
def main():
  conversation = ConversationChain(
      llm=llm,
      verbose=True,
      memory=ConversationBufferMemory()
  )
  st.title("E.V.A.")
  docs = st.sidebar.file_uploader("Insira seus arquivos", type="pdf", accept_multiple_files=True)
  
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
      conversation.predict(input=prompt)
      stream = conversation.memory.buffer_as_messages[-1].content
      st.write(stream)
    st.session_state.messages.append({"role": "assistant", "content": stream})
    
        
if __name__ == '__main__':
  main()
  
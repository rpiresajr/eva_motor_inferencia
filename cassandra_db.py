from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from langchain_community.vectorstores import Cassandra
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv
import os
from pytz import timezone
from datetime import datetime
from langchain.docstore.document import Document
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback

from open_ai import Open_AI

load_dotenv(find_dotenv())

class CassandraDB:
  def __init__(self):
    self.keyspace = os.environ.get("CASSANDRA_KEYSPACE")
    self.vector_table = os.environ.get("CASSANDRA_VECTOR_TABLE")
    self.fuso_horario = timezone('America/Sao_Paulo')
    self.auth_provider = PlainTextAuthProvider(username=os.environ.get("CASSANDRA_USER"), password=os.environ.get("CASSANDRA_PASS"))
    self.cluster = Cluster([os.environ.get("CASSANDRA_CLUSTER")], auth_provider=self.auth_provider)
    self.session = self.cluster.connect()
    self.ia = Open_AI(self)

  def write_vectors_from_text(self, text, filename):
    page = 0
    date_time = datetime.now().astimezone(self.fuso_horario).strftime('%Y-%m-%d')
    docs = []
    
    chunks = self.ia.text_splitter.split_text(text)
    
    for chunk in chunks:
      page += 1
      metadata = {'source': filename, 'page': f"{page}", 'data': f"{date_time}",  }
      doc = Document(page_content=chunk, metadata=metadata)
      docs.append(doc)
    
    vstore = self.ia.load_vectors_db()
    inserted_ids = vstore.add_documents(docs)
    for id in range(len(inserted_ids)):
      print(inserted_ids[id])
      
  def get_response(self, filtered_docs, question) -> str:
    chain = load_qa_chain(self.ia.llm, chain_type="stuff")
    with get_openai_callback() as cb:
      response = chain.run(input_documents=filtered_docs, question=question)
      response = response.replace("\n", " ").strip()
      print(cb)
      return response
    
  def search(self, question):
    vectorstore = self.ia.load_vectors_db()
    documents = vectorstore.similarity_search(question, k=3)
    resp = self.get_response(documents, question)
    return resp
    
    
    # retriever = vectorstore.as_retriever(search_kwargs=dict(k=1))
    # memory = VectorStoreRetrieverMemory(retriever=retriever)
    
    
    
    # _DEFAULT_TEMPLATE = """The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.

    # Relevant pieces of previous conversation:
    # {history}

    # Current conversation:
    # Human: {input}
    # AI:"""
    # PROMPT = PromptTemplate(
    #     input_variables=["history", "input"], template=_DEFAULT_TEMPLATE
    # )
    
    # conversation_with_summary = ConversationChain(
    #   llm=self.ia.llm,
    #   prompt=PROMPT,
    #   memory=memory,
    #   verbose=False
    # )
    # text = conversation_with_summary.predict_and_parse(input=question)
    # # #conversation_with_summary.predict(input=question)
    # # #conversation_with_summary.memory
    # return text
    

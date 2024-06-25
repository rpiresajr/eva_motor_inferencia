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
import uuid;

load_dotenv(find_dotenv())
FIELD_LIST = "row_id, session_id, created_date, created_at, attributes_blob, body_blob, vector, metadata_s"

class CassandraDB:
  def __init__(self):
    self.keyspace = os.environ.get("CASSANDRA_KEYSPACE")
    self.vector_table = os.environ.get("CASSANDRA_VECTOR_TABLE")
    self.questions_table = os.environ.get("CASSANDRA_QUESTIONS_TABLE")
    self.fuso_horario = timezone('America/Sao_Paulo')
    self.auth_provider = PlainTextAuthProvider(username=os.environ.get("CASSANDRA_USER"), password=os.environ.get("CASSANDRA_PASS"))
    self.cluster = Cluster([os.environ.get("CASSANDRA_CLUSTER")], auth_provider=self.auth_provider)
    self.session = self.cluster.connect()
    self.ia = Open_AI(self)
    
  def insert_question(self, sessionId, text, page, vector):
    table_name = self.questions_table
    row_id = uuid.uuid4().hex
    short_date = datetime.now().astimezone(self.fuso_horario).strftime('%Y-%m-%d')
    long_date = datetime.now()
    metadata = {'source': sessionId, 'page': f"{page}", 'data': f"{long_date}",  }
    
    stmt = self.session.prepare(f"INSERT INTO {self.keyspace}.{table_name} ({FIELD_LIST}) VALUES (?,?,?,?,?,?,?,?);")
    self.session.execute(stmt, [row_id, sessionId, short_date, long_date, '', text, vector, metadata])

  def write_vectors_from_text(self, text, filename):
    ids = self.get_dup_documents(filename)
    self.delete_dup(ids)
    page = 0
    # date_time = datetime.now().astimezone(self.fuso_horario).strftime('%Y-%m-%d')
    date_time = self.unix_time_millis(datetime.now())
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
      
  def write_questions_from_text(self, text, sessionId):
    vector = self.ia.get_embedding(text)
    self.insert_question(str(sessionId), text, 1, vector)
    print("ok")
    # page = 0
    # date_time = datetime.now().astimezone(self.fuso_horario).strftime('%Y-%m-%d')
    # docs = []
    
    # chunks = self.ia.text_splitter.split_text(text)
    
    # for chunk in chunks:
    #   page += 1
    #   metadata = {'sessionId': sessionId, 'page': f"{page}", 'data': f"{date_time}",  }
    #   doc = Document(page_content=chunk, metadata=metadata)
    #   docs.append(doc)
    
    # vstore = self.ia.load_questions_db()
    # inserted_ids = vstore.add_documents(docs)
    # for id in range(len(inserted_ids)):
    #   print(inserted_ids[id])
      
  def get_response(self, filtered_docs, question) -> str:
    chain = load_qa_chain(self.ia.llm, chain_type="stuff")
    with get_openai_callback() as cb:
      response = chain.run(input_documents=filtered_docs, question=question)
      response = response.replace("\n", " ").strip()
      print(cb)
      return response
    
  def search(self, question):
    vectorstore = self.ia.load_vectors_db()
    documents = vectorstore.similarity_search(question, k=2)
    resp = self.get_response(documents, question)
    return resp
    
  def get_documents(self, question):
    vectorstore = self.ia.load_vectors_db()
    documents = vectorstore.similarity_search(question, k=3)
    return documents
  
  def delete_dup(self, rows):
    table_name = self.vector_table
    
    if not table_name:
      raise ValueError('Necessário o nome da tabela.')
    
    ids = '('
    for row in rows:
      ids += f"'{row.row_id}',"
    ids = ids[:-1]
    ids = ids + ")"
    print(ids)  
    self.session.execute(f"DELETE FROM {self.keyspace}.{table_name} WHERE row_id IN {ids};")
  
  def get_dup_documents(self, filename):
    table_name = self.vector_table
    
    if not table_name:
      raise ValueError('Necessário o nome da tabela.')
    
    stmt = self.session.prepare(f"select row_id from {self.keyspace}.{table_name} WHERE metadata_s['source'] = '{filename}' ALLOW FILTERING;")
    return self.session.execute(stmt)
  
  def get_sessions(self):
    table_name = self.questions_table
    date_time = datetime.now().astimezone(self.fuso_horario).strftime('%Y-%m-%d')
    
    if not table_name:
      raise ValueError('Necessário o nome da tabela.')
    stmt = self.session.prepare(f"select created_date, session_id, created_at, body_blob from {self.keyspace}.{table_name} WHERE created_date = '{date_time}' ALLOW FILTERING;")
    return self.session.execute(stmt)
  
  def unix_time(self, dt):
    epoch = datetime.datetime.utcfromtimestamp(-3)
    delta = dt - epoch
    return delta.total_seconds()

  def unix_time_millis(self, dt):
    return int(self.unix_time(dt) * 1000.0)
    
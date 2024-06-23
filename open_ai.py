from dotenv import load_dotenv, find_dotenv
import os
#from openai import OpenAI
from langchain_openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Cassandra

load_dotenv(find_dotenv())

class Open_AI:
  def __init__(self, db):
    self.db = db
    self.embedding = OpenAIEmbeddings(model='text-embedding-3-small')
    self.llm = OpenAI()
    self.text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=50, length_function=len)
    
    
  def load_vectors_db(self):
    vstore = Cassandra(
        embedding=self.embedding,
        table_name=self.db.vector_table,
        keyspace=self.db.keyspace,
        session=self.db.session
    )
    return vstore
    
  
    
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os.path
import pickle
from googleapiclient.discovery import build
from email.header import decode_header
from email.mime.text import MIMEText
import base64

# Escopos necessários
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']  # Este escopo permite ler, enviar, deletar e buscar e-mails

class GmailAPI:
    def __init__(self):
        self.service = self.gmail_authenticate()
        
    def get_subject_from_message(self, message):
        """
        Extract the subject from a message object.
        """
        headers = message.get('payload', {}).get('headers', [])
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), None)
        if subject:
            subject = decode_header(subject)[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode('utf-8')
        return subject

    def gmail_authenticate(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return build('gmail', 'v1', credentials=creds)

    def create_message(self, sender, to, subject, message):
        message = MIMEText(message)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, sender: str, to: str, subject: str, message: str):
        try:
            message = self.create_message(sender, to, subject, message)
            message = self.service.users().messages().send(userId="me", body=message).execute()
            return f'Message Id: {message["id"]}'
        except Exception as error:
            return f'An error occurred: {error}'

    def get_message(self, msg_id: str):
        try:
            message = self.service.users().messages().get(userId="me", id=msg_id).execute()
            return message
        except Exception as error:
            return f'An error occurred: {error}'

    def search_messages(self, query: str ='', max_results: int =5):
        print(query)
        try:
            response = self.service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = []
            print(response)
            for msg in response['messages']:
                message = self.service.users().messages().get(userId="me", id=msg['id'], format='metadata', metadataHeaders=['Subject']).execute()
                subject = self.get_subject_from_message(message)
                messages.append({'id': msg['id'], 'subject': subject, 'snippet': message.get('snippet')})
                
            return messages
        except Exception as error:
            print(error)
            return f'An error occurred: {error}'
 
    def delete_message(self, msg_id: str):
        try:
            self.service.users().messages().delete(userId="me", id=msg_id).execute()
            return f'Message with id: {msg_id} deleted successfully.'
        except Exception as error:
            print(error)
            return f'An error occurred: {error}'



# Exemplo de uso da classe
# gmail_api = GmailAPI()
# messages = gmail_api.search_messages(query='important', max_results=10)
# for msg in messages:
#     print(f'Message ID: {msg["id"]}')



#service = gmail_authenticate()
#query = 'subject:important'  
#max_results = 10
#found_messages = search_messages(service, query=query, max_results=max_results)

#for message in found_messages:
    #print(f'Message ID: {message["id"]}')




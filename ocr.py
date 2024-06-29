from pdf2image import convert_from_bytes
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from pytz import timezone
from datetime import datetime
import io

class OCR:
  def __init__(self):
    self.fuso_horario = timezone('America/Sao_Paulo')
    y, m, d = datetime.now().astimezone(self.fuso_horario).strftime('%Y-%m-%d').split('-')
    
  def extract_image_to_text_by_generated_image(self, file):
    text = ''
    doc = fitz.open(stream=file.getvalue())
    images = convert_from_bytes(doc.stream)
    for i in range(len(images)):
      text += pytesseract.image_to_string(images[i], lang='por')
      
    return text
  
  def extract_from_images(self, file):
    doc = fitz.open(stream=file.getvalue())
    ocr_result = ''
    
    for page_number in range(doc.page_count):
      page = doc.load_page(page_number)

      # Extrair as imagens da página
      image_list = page.get_images(full=True)

      for img_index, img in enumerate(image_list):
          xref = img[0]
          base_image = doc.extract_image(xref)
          image_bytes = base_image["image"]

          # Converter bytes para uma imagem PIL
          image = Image.open(io.BytesIO(image_bytes))

          # Salvar a imagem extraída (opcional)
          # image.save(f"imagem_extraida_{page_number}_{img_index}.png")

          # Aplicar OCR com Tesseract
          ocr_result += '\n' + pytesseract.image_to_string(image, lang='por')  # 'por' para português

          # Imprimir o resultado do OCR
          # print(f"Resultado do OCR para a imagem {img_index} da página {page_number}:\n")
          # print(ocr_result)
    return ocr_result
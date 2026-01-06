from googletrans import Translator

translator = Translator()

tamil_text = "தமிழ் மொழியில் எழுதப்பட்ட உரையை ஆங்கிலத்துக்கு மொழிபெயர்க்க"
tanglish_text = "tamizh mozhi-il ezhuthapatta uraiyai aangilathukku mozhipeyarkka"

translated_tamil = translator.translate(tamil_text, src='ta', dest='en')
translated_tanglish = translator.translate(tanglish_text, src='auto', dest='en')

print("Tamil to English:", translated_tamil.text)
print("Tanglish to English:", translated_tanglish.text)

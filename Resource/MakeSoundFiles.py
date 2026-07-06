from gtts import gTTS
import os

language = 'ru'
text = "Тестирование платы успешно завершено"
speech = gTTS(text = text, lang = language, slow = False)
speech.save("TestIsSuccessful.mp3")

text = "Тестирование платы завершено с ошибкой"
speech = gTTS(text = text, lang = language, slow = False)
speech.save("TestIsFailed.mp3")


"""The three pages of OptiSense, one package each: work (“Model & solution”, the start page),
learn (“Learn & practise”) and guide (“Guide”).

Every page package holds its own texts (texts.py), layout (ui.py) and server part (server), and the
browser files of the same name in www/ (work.css/.js, learn.css/.js, guide.css/.js).
The package files stay free of imports: i18n reads the texts of all pages.
"""

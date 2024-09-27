import os
import subprocess
from pdf2image import convert_from_path
from random import shuffle
import pandas as pd
import zipfile
import streamlit as st

def replace_umlaute(latex_content):
    for c, r in [('ä', '\\"a'), ('ö', '\\"o'), ('ü', '\\"u'), ('Ä', '\\"A'), ('Ö', '\\"O'), ('Ü', '\\"u')]:
        latex_content = latex_content.replace(c, r)
    return latex_content

def createStringRow(row_number):
    s = ''
    for n in range(1, grid_size + 1):
        s += 'C' + str(row_number) + str(n) + ' & '
    s = s[:-3]
    return s

def create_table_image(content_list):
    latex_content = r'''
    \documentclass[border=5pt]{standalone}
    \usepackage[utf8]{inputenc}
    \usepackage{easytable}
    \pagenumbering{gobble}
    \renewcommand{\familydefault}{\sfdefault}
    \begin{document}
        \begin{TAB}(e,1cm,1cm){|CN|}{|CN|}
        GRID    
        \end{TAB}
    \end{document}
    '''

    s = 'c:'*grid_size
    s = s[:-1]
    latex_content = latex_content.replace('CN', s)

    s = ''
    for n in range(1, grid_size + 1):
        s += 'Z' + str(n) + r' \\' + '\n\t'
    s = s[:-5]
    latex_content = latex_content.replace('GRID', s)

    for n in range(1, grid_size + 1):
        latex_content = latex_content.replace('Z' + str(n), createStringRow(n))
    
    print(1, latex_content)

    shuffle(content_list)
    for cell in ["C" + str(r) + str(c) for r in range(1, grid_size+1) for c in range(1, grid_size+1)]:
        content = content_list.pop()
        latex_content = latex_content.replace(cell, content)

    print(2, latex_content)
    
    latex_content = replace_umlaute(latex_content)

    with open('tabelle.tex', 'w') as file:
        file.write(latex_content)

    subprocess.run(['pdflatex', 'tabelle.tex'])

    images = convert_from_path('Tabelle.pdf', dpi=1000)
    return images[0]

def create_beamer(content_list):
    progress_bar.progress((n+1)/(n+2), text="Erstelle Folien ...")
    latex_content = r'''
    \documentclass[20pt]{beamer}
    \usepackage[utf8]{inputenc}
    \title{\Huge{Bingo}}
    \date{}
    \begin{document}
        \frame{\titlepage}
    ''' + len(content_list)*r'''    
        \begin{frame}
            \begin{center}
                _C_
            \end{center}
        \end{frame}
    ''' + r'''
    \end{document}
    '''

    shuffle(content_list)
    while len(content_list):
        content = content_list.pop()
        latex_content = latex_content.replace('_C_', content, 1)

    latex_content = replace_umlaute(latex_content)

    with open('beamer.tex', 'w') as file:
        file.write(latex_content)

    subprocess.run(['pdflatex', 'beamer.tex'])

def create_tables(path_list):
    progress_bar.progress(100, text="Erstelle Bingo-Felder ...")
    latex_content = r'''
    \documentclass{article}
    \pagenumbering{gobble}
    \usepackage[a4paper, left=2cm, right=2cm]{geometry}
    \usepackage{graphicx}
    \begin{document}
    ''' + len(path_list)*r''' 
        \newpage
        \center
        \Huge Bingo
        \includegraphics[width=\textwidth]{_C_}
    ''' + r'''
    \end{document}
    '''

    while len(path_list):
        path = path_list.pop()
        latex_content = latex_content.replace('_C_', path, 1)

    with open('bingo.tex', 'w') as file:
        file.write(latex_content)

    subprocess.run(['pdflatex', 'bingo.tex'])

def convert_fraction(row):
    fraction = row.split('/')
    numerator = fraction[0]
    denominator = fraction[1]
    return '$\\frac{_A_}{_B_}$'.replace('_A_', numerator).replace('_B_', denominator)

def convert_number(row):
    return '$' + str(row) + '$'

def convert_formula(row):
    row = row.replace('*', ' \\text\{\\cdot\} ')
    row = row.replace('/', ' \\div ')
    row = row.replace(':', ' \\div ')
    return '$' + str(row) + '$'

def clean():
    os.remove('tabelle.tex')
    os.remove('tabelle.log')
    os.remove('tabelle.aux')
    os.remove('Tabelle.pdf')

    os.remove('beamer.tex')
    os.remove('beamer.log')
    os.remove('beamer.aux')
    os.remove('beamer.nav')
    os.remove('beamer.out')
    os.remove('beamer.snm')
    os.remove('beamer.toc')

    os.remove('bingo.tex')
    os.remove('bingo.log')
    os.remove('bingo.aux')

    for image_path in image_path_list:
        os.remove(image_path)

file = st.file_uploader("Choose a file")

if file == None:
    st.stop()

df = pd.read_excel(file)
st.write(df)

grid_size = st.slider("Spalten/Zeilen", min_value=2, max_value=10, value=5, step=1)

types = ('Text', 'Zahl', 'Formel', 'Bruch')
type_question = st.selectbox('Format Frage', types)
type_answer = st.selectbox('Format Antwort', types)
if type_question == None or type_answer == None:
    st.stop()

questions = list()
answers = list()
for index, row in df.iterrows():
    if type_question == 'Text':
        questions.append(row['Frage'])
    elif type_question == 'Zahl':
        questions.append(convert_number(row['Frage']))
    elif type_question == 'Formel':
        questions.append(convert_formula(row['Frage']))
    elif type_question == 'Bruch':
        questions.append(convert_fraction(row['Frage']))

    if type_answer == 'Text':
        answers.append(row['Antwort'])
    elif type_answer == 'Zahl':
        answers.append(convert_number(row['Antwort']))
    elif type_answer == 'Formel':
        answers.append(convert_formula(row['Antwort']))
    elif type_answer == 'Bruch':
        answers.append(convert_fraction(row['Antwort']))

n = st.number_input('Anzahl SuS', 1, 100, value=30, step=1)
image_path_list = list()

if not st.checkbox('Start'):
    st.stop()

with st.spinner('Erstelle Dateien...'):
    progress_bar = st.progress(0)
    for i in range(1, n+1):
        progress_bar.progress(i/(n+2), text="Erstelle Bilder ...")
        image = create_table_image(answers.copy())
        image_path = 'Tabelle' + str(i).zfill(2) + '.png'
        image.save(image_path, 'PNG')
        image_path_list.append(image_path)

    create_beamer(questions.copy())
    create_tables(image_path_list.copy())

    progress_bar.empty()

with zipfile.ZipFile('bingo.zip', 'w') as zip_file:
    zip_file.write("bingo.pdf")
    zip_file.write("beamer.pdf")

with open("bingo.zip", "rb") as zip_file:
    zip = zip_file.read()

st.download_button(label="Download", data=zip, file_name='bingo.zip', mime='zip')

# clean()
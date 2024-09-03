from bs4 import BeautifulSoup
import csv
import os
import re

#function to read files
def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return BeautifulSoup(content, 'lxml')

#function to extract text from html elements, returns string
def extract_text(element):
    if element:
        return ' '.join(element.stripped_strings)
    return ''

#function to extract filename, returns string
def get_filename(file_path):
    file_name = file_path.split('Training_Filings/') [-1]
    return file_name

#function to execute the procceses to get eps, returns an eps
def get_eps(soup):
    eps = None

    eps_keywords = ['earnings', 'income', 'loss']
    eps_pershare = ['per', 'share']
    eps_string = ['eps']
    priority_keywords = ['net', 'total', 'gaap basic', 'gaap diluted', 'basic', 'diluted']
    nle_string = ['net (loss) earnings']

    for table in soup.find_all('table'):

        #checking to see if table is a paragraph table - if it is, skip
        rows = table.find_all('tr')
        num_chars = 0
        total_chars = 0
        num_ratio = 0.14
        for row in rows:
            elements = row.find_all(['td', 'th'])
            for element in elements:
                element_text = extract_text(element).lower()
                for char in element_text:
                    if char.isalpha():
                        total_chars+=1
                    elif char.isdigit():
                        total_chars+=1
                        num_chars+=1
        if total_chars > 0:
            if (num_chars >= 100) and (num_chars/total_chars > num_ratio):
        
                # Track the best EPS row for the current table
                table_eps_row = None
                table_eps_rows = []
                table_eps_row_texts = []
                table_eps_score = len(priority_keywords)+1

                #checking for eps key and finding eps row
                for row in rows:
                    elements = row.find_all(['td', 'th'])
                    for element in elements:
                        element_text = extract_text(element).lower().strip()
                        has_epskey = any(keyword in element_text for keyword in eps_keywords)
                        has_persharekey = all(keyword in element_text for keyword in eps_pershare)
                        has_epsstring = any(keyword in element_text for keyword in eps_string)
                        has_nlestring = any(keyword in element_text for keyword in nle_string)
                        
                        if (has_epskey and has_persharekey) or has_epsstring or has_nlestring:
                            table_eps_row_texts.append(element_text)
                            table_eps_rows.append(row)
                            break

                    if table_eps_rows:
                        for i in table_eps_row_texts:
                            if i is None:
                                continue
                            row_score = get_priority(i, priority_keywords)
                            if row_score < table_eps_score:
                                table_eps_row = row
                                table_eps_score = row_score
                        
            
                #checking the table and getting eps
                if table_eps_row:
                    table_eps = row_to_eps(table_eps_row)
                    if table_eps == 'empty':
                        while table_eps == 'empty':
                            next_row = table_eps_row.find_next('tr')
                            if next_row:
                                table_eps_row = next_row
                                table_eps = row_to_eps(next_row)
                                if (table_eps != 'empty') and (table_eps is not None):
                                    return table_eps
                    if table_eps is not None:
                        eps = table_eps
                        return eps
    return None

#function to get the priority of a row, returns int
def get_priority(row_text, priority_keywords):
    row_text = row_text.lower()
    for i, key in enumerate(priority_keywords):
        if key in row_text:
            return i
    return len(priority_keywords)

#function to find eps in row text, returns float or None or "empty"
def row_to_eps(row):
    eps = None
    element_list = []
    elements = row.find_all(['td', 'th'])
    for element in elements:
        element_text = extract_text(element).lower()

        if element_text is None:
            element_list.append(element_text)

        eps_float = convert_float(element_text)

        if eps_float is not None and abs(eps_float) < 10:
            eps = eps_float
            return eps
    if all(i is None for i in element_list):
        return "empty"
    return None

#function to convert text to float, returns float or None
def convert_float(element_text):
    if element_text is None:
        return 'empty'
    
    if not isinstance(element_text, str):
        element_text = str(element_text)
    
    element_text = element_text.replace('$', '').strip()
    
    if '(' in element_text and ')' in element_text:
        element_text = '-' + element_text.strip('()')

    clean_text = re.sub(r'[^\d.-]', '', element_text)

    match = re.search(r'-?\d*\.?\d+', clean_text)

    if match:
        num_str = match.group()
        try:
            return float(num_str)
        except ValueError:
            return None
    return None

#function to write to csv
def write_csv(data, output):
    with open(output, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filepath', 'EPS'])
        for row in data:
            writer.writerow(row)

#main function
def main(file_paths, output):
    tuples = []
    for file_path in os.listdir(file_paths):
        file_path = os.path.join(file_paths, file_path)
        file_name = get_filename(file_path)
        soup = read_file(file_path)
        eps = get_eps(soup)
        tuples.append([file_name, eps])
    write_csv(tuples, output)

if __name__ == '__main__':
    main('/Users/jason/Documents/Vscode/TQI_assessment/Training_Filings', 'output.csv')
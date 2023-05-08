import kfp
from kfp.v2 import dsl
from kfp.v2.dsl import (
    Input,
    Output,
    Artifact,
    Dataset,
    Metrics,
    HTML,
)
from datetime import date, timedelta

# Define the download component
@dsl.component(
    base_image='python:3.9-alpine',
    packages_to_install = [
        "minio",
        "bs4",
        "trafilatura",
        "plotly"
    ]
)
def download_onions(from_day:int, from_month:int, from_year:int, cleaned_onions: Output[Artifact], metrics: Output[Metrics], plot: Output[HTML]):
    from minio import Minio
    from datetime import date, timedelta
    from bs4 import BeautifulSoup
    from trafilatura import extract
    import string
    import pickle
    import plotly.graph_objs as go
    import plotly.io as pio

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def get_title(soup):
        if soup.findAll("title"):
            return soup.find("title").string
        else:
            return ''

    def get_description(soup):
        if soup.findAll("meta", attrs={"name": "description"}):
            return soup.find("meta", attrs={"name": "description"}).get("content")
        else:
            return ''

    client = Minio(
        endpoint="minio.minio:9000",
        secure=False,
        access_key='processing',
        secret_key=',TkTV3c7:e6#e}HwiD4R'
    )
    
    start_date = date(from_year, from_month, from_day)
    today = date.today()

    total_onions = 0
    empty_onions = 0
    bad_encoded_onions = 0
    debug = 0

    htmls = {}
    for single_date in daterange(start_date, today):
        daily_onions = 0
        if single_date < today:
            print("Downloading data from",single_date.strftime("%d-%m-%Y"), "...")
            for document in client.list_objects(bucket_name="onions", prefix=f"{single_date.year}/{single_date.month}/{single_date.day}/htmls/"):
                total_onions+=1
                daily_onions+=1
                try:
                    response = client.get_object("onions", document.object_name)
                    html = response.data.decode("utf-8")
                    bs = BeautifulSoup(html, 'html.parser')

                    title = get_title(bs)
                    if title is None:
                        title = ''
                    description = get_description(bs)
                    if description is None:
                        description = ''
                    content = ''
                    content = extract(html, include_formatting=False, include_links=False, include_images=False, include_tables=False)
                    if content is None:
                        content = ''
                    title_description_content = []
                    if title == description:
                        title_description_content = [title, content]
                    else:
                        title_description_content = [title, description, content]
                    text = ''
                    for t in title_description_content:
                        if t != '':
                            if t[:-1] != text:
                                if t[-1] not in string.punctuation:
                                    t = t+'. '
                                else:
                                    t = t+' '
                                text = "{0}{1}".format(text, t)

                    if text == '':
                        empty_onions+=1
                    #print(f"[Title] {title} [Description] {description}")
                    htmls[document.object_name] = text

                    if total_onions % 100 == 0:
                        print(f"Processed {total_onions} onions...")
                        #break
                    
                except UnicodeDecodeError as err:
                    bad_encoded_onions+=1
                    print(f"[Error] {err}")
                    htmls[document.object_name] = 'bad encoded'
                    continue
                except Exception as err:
                    bad_encoded_onions+=1
                    print(f"[Error] {err}")
                    htmls[document.object_name] = 'bad encoded'
                    continue
                finally:
                    response.close()
                    response.release_conn()
            
            print("Downloaded onions in",single_date.strftime("%d-%m-%Y"),"->",daily_onions)


    yesterday = today - timedelta(days=1)
    fig = go.Figure(data=[go.Pie(labels=['Cleaned onions', 'Empty onions', 'Bad-encoded onions'],
                                 values=[total_onions-empty_onions-bad_encoded_onions, empty_onions, bad_encoded_onions])])
    fig.update_layout(title=f'Downloaded onions from {from_day}/{from_month}/{from_year} to {yesterday.day}/{yesterday.month}/{yesterday.year}')
    
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig))

    metrics.log_metric('Total onions', total_onions)
    metrics.log_metric('Empty onions', empty_onions)
    metrics.log_metric('Bad-encoded onions', bad_encoded_onions)
    metrics.log_metric('Cleaned onions', total_onions-empty_onions-bad_encoded_onions)

    with open(cleaned_onions.path, 'wb') as f:
        pickle.dump(htmls, f)


# Define the download component
@dsl.component(
    base_image='python:3.9-alpine',
    packages_to_install = [
        "minio",
        "plotly"
    ]
)
def version_onion_dataset(from_day:int, from_month:int, from_year:int, cleaned_onions: Input[Artifact], metrics: Output[Metrics], plot: Output[HTML]):
    from minio import Minio
    import pickle
    from datetime import date, timedelta
    from minio.error import S3Error
    import io
    import plotly.graph_objs as go
    import plotly.io as pio

    client = Minio(
        endpoint="minio.minio:9000",
        secure=False,
        access_key='processing',
        secret_key=',TkTV3c7:e6#e}HwiD4R'
    )
    
    with open(cleaned_onions.path, 'rb') as f:
        new_onions = pickle.load(f)
   

    # download previous version
    first_version = date(2022, 11, 15)                          # threshold of first version
    last_date = date(from_year, from_month, from_day)           # dates to check from now to origin
    last_dataset = None                                         # indicates if previous version found
   
    while (last_date > first_version and last_dataset is None):
        last_date = last_date - timedelta(days=1)
        print("Checking version of", last_date.strftime("%d-%m-%Y"), "...")
        try:
            response = client.get_object("datasets",f"{last_date.year}/{last_date.month}/{last_date.day}/cleaned_onions/cleaned_onions.pickle")
            print("Downloaded version of", last_date.strftime("%d-%m-%Y"))
            last_dataset = pickle.loads(response.read())
        except S3Error as exc:
            print("It does not exist! Next...", exc)
            continue

    # update to new version 
    if last_dataset is None:
        updated_dataset = new_onions
    else:
        last_dataset.update(new_onions)
        updated_dataset = last_dataset
    
    total_collected_onions = 0
    total_empty_onions = 0
    total_bad_encoded_onions = 0
    for onion, text in updated_dataset.items():
        total_collected_onions +=1
        if text == '':
            total_empty_onions+=1
        elif text == 'bad encoded':
            total_bad_encoded_onions+=1


    ##### write to MinIO
    versioning_date = date.today() - timedelta(days=1)    # date for new versioning
    
    bytes_file = pickle.dumps(updated_dataset)
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/cleaned_onions/cleaned_onions.pickle",
            data=io.BytesIO(bytes_file),
            length=len(bytes_file))
    
    stats = f"Total collected onions: {total_collected_onions}\nTotal empty onions: {total_empty_onions}\nTotal bad encoded: {total_bad_encoded_onions}\nTotal cleaned onions: {total_collected_onions-total_empty_onions-total_bad_encoded_onions}"
    stats_bytes = stats.encode('utf-8')
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/cleaned_onions/stats.txt",
            data=io.BytesIO(stats_bytes),
            length=len(stats_bytes))

    #### metrics and plot
    fig = go.Figure(data=[go.Pie(labels=['Total empty onions', 'Total bad encoded', 'Total cleaned onions'],
                                 values=[total_empty_onions, total_bad_encoded_onions, total_collected_onions-total_empty_onions-total_bad_encoded_onions])])
    fig.update_layout(title=f'Total onions until {versioning_date.day}/{versioning_date.month}/{versioning_date.year}')
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig))

    metrics.log_metric('Total collected onions', total_collected_onions)
    metrics.log_metric('Total empty onions', total_empty_onions)
    metrics.log_metric('Total bad encoded', total_bad_encoded_onions)
    metrics.log_metric('Total cleaned onions', total_collected_onions-total_empty_onions-total_bad_encoded_onions)


# Define the preprocessing component
@dsl.component(
    base_image='python:3.9-alpine',
    packages_to_install = [
        "nltk",
        "plotly"
    ]
)
def preprocess_onions(from_day:int, from_month:int, from_year:int, cleaned_onions: Input[Artifact], preprocessed_onions: Output[Artifact], metrics: Output[Metrics], plot: Output[HTML]):
    import pickle
    import re
    import string
    from datetime import date, timedelta
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    import plotly.graph_objs as go
    import plotly.io as pio
    nltk.download('punkt')

    def find_onion_address(string):
        # Use a regular expression to match a TOR onion service address
        pattern = r'\b[a-z2-7]{16,56}\.onion\b'
        match = re.search(pattern, string)
        return match is not None

    def find_pgp_key(sentence):
        # Use a regular expression to search for an email address in the input string
        regex = re.compile(r"-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----?")
        # Use the re.search() method to find a match for the regular expression
        match = re.search(regex, sentence)
        # Return a boolean value indicating whether a match was found
        return bool(match)
    
    def find_email_address(sentence):
        # Use a regular expression to search for an email address in the input string
        regex = re.compile(r"\s[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\s")
        # Use the re.search() method to find a match for the regular expression
        match = re.search(regex, sentence)
        # Return a boolean value indicating whether a match was found
        return bool(match)
    
    def find_monetary_value(sentence):
        # Use a regular expression to search for a monetary value in the input string
        regex = re.compile(r"(%|USD|EUR|\$)\s?\d+(?:[.,]\d{3})*|\d+(?:[.,]\d)*\s?(USD|EUR|\$|BTC|%)")
        # Use the re.search() method to find a match for the regular expression
        match = re.search(regex, sentence)
        # Return a boolean value indicating whether a match was found
        return bool(match)

    def find_url(sentence):
        # Use a regular expression to search for a URL in the input string
        # regex = re.compile(r"[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
        regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https:// or ftp:// or ftps://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
            r'(localhost)|' # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        # Use the re.search() method to find a match for the regular expression
        match = re.search(regex, sentence)
        # Return a boolean value indicating whether a match was found
        return bool(match)
    
    def find_bitcoin_address(sentence):
        # Use a regular expression to search for a Bitcoin address in the input string
        regex = re.compile(r"([13]|bc1)[A-HJ-NP-Za-km-z1-9]{27,34}")
        # Use the re.search() method to find a match for the regular expression
        match = re.search(regex, sentence)
        # Return a boolean value indicating whether a match was found
        return bool(match)
    
    def is_web_tag(sentence):
        tags = ["Contact", "Logic", "FAQ", "Login", "About", "Services", "Privacy", "Term", "Support", "Blog", "Team", "Contact Us", "Sign Up", "Sign In", "Login", "Register", "Dark Web", "TOR", "Onion Router", "Hidden Services", "Encryption", "Anonymity"]
        # Use a regular expression to search for words in the given sentence in the array of tags
        return sentence in tags
    
    def check_for_words(text):
        # Use a regular expression to match any word that contains at least one alphabetical character
        pattern = r'\b[a-zA-Z]+\b'
        match = re.search(pattern, text)
        return match is not None
    
    def remove_line_breaks_and_tabs(text):
        # Replace line breaks with spaces
        text = text.replace('\n', '. ')

        # Replace tabs with spaces
        text = text.replace('\t', '. ')

        return text

    def remove_special_characters(text):
        # Use the string.translate() method to remove specific characters from the input string
        text = text.translate(str.maketrans('', '', '<#*_="+><'))
        return text
    
    def remove_non_word_characters_at_beginning(s):
        # Make a translation table to remove non-word characters
        table = s.maketrans('', '', string.punctuation + string.whitespace + '0123456789')

        # Split the string into a list of words
        words = s.split()

        # Find the first word in the list
        for i, word in enumerate(words):
            # Use the translation table to remove non-word characters from the beginning of the word
            stripped = word.lstrip(string.punctuation + string.whitespace + '0123456789')
            # If the stripped word is not empty, it is the first word
            if stripped:
                words[i] = stripped
                break
            # Otherwise, remove the word from the list
            else:
                words.pop(i)

        # Join the words back into a single string, with a single space between each word
        return ' '.join(words)
    
    def remove_spaces_before_punctuation(string):
        # Split the string into a list of characters
        chars = list(string)

        # Initialize an empty list to store the modified characters
        fixed_chars = []

        # Iterate through the characters
        for i, char in enumerate(chars):
            # If the character is a punctuation mark and the previous character is a space,
            # skip the space and add the punctuation mark to the list of modified characters
            if char in ['!', '?', ',', ';', ':'] and i > 0 and chars[i-1] == ' ':
                fixed_chars[-1] = char
            # If the character is not a punctuation mark, or if it is a punctuation mark but the previous character is not a space,
            # add the character to the list of modified characters
            else:
                fixed_chars.append(char)

        # Join the modified characters into a single string and return it
        return ''.join(fixed_chars)

    def deduplicate_words(sentence):
        # Split the sentence into a list of words
        words = sentence.split(" ")
        
        # Create an empty list to store the deduplicated words
        deduplicated = [words[0]]
        
        # Loop through each word in the list of words
        for word in words[1:]:
            # If the current word is not the same as the previous word, add it to the list of deduplicated words
            if word != deduplicated[-1]:
                deduplicated.append(word)
        # Join the deduplicated words into a string and return it
        return " ".join(deduplicated)
    
    def compact_repeated_spaces(input_string):
        # Use the re.sub() method to remove repeated spaces from the input string
        output_string = re.sub(r'\s+', ' ', input_string)
        return output_string
    
    def modify_string(input_string):
        # Use the string.replace() method to replace certain characters or sequences of characters in the input string
        input_string = input_string.replace('#','.')
        input_string = input_string.replace(' -','. ')
        input_string = input_string.replace(':)','')
        input_string = input_string.replace(' _','. ')
        input_string = input_string.replace(' |','. ')
        input_string = input_string.replace(' !','. ')
        input_string = input_string.replace('!','. ')
        input_string = input_string.replace('?','? ')
        input_string = input_string.replace(' ?','? ')
        input_string = input_string.replace(' :',':')
        input_string = input_string.replace('( ',' (')
        input_string = input_string.replace(' )',') ')
        input_string = input_string.replace(' ;','. ')
        input_string = input_string.replace(';','. ')
        input_string = input_string.replace(' .','. ')
        input_string = input_string.replace(':.',':')
        input_string = input_string.replace('?.','?')
        input_string = input_string.replace('-.','.')
        input_string = compact_repeated_spaces(input_string)
        return input_string.strip()
    
    def remove_repeating_punctuation(string):
        # Use a regular expression to match one or more repetitions of any punctuation character
        pattern = r'([^\w\s])\1+'
        # Replace all repetitions with a single instance of the punctuation character
        return re.sub(pattern, r'\1', string)

    def deduplicate_sentences(text):
        # Split the text into a list of sentences
        sentences = text.split(".")
        
        # Create an empty list to store the deduplicated sentences
        deduplicated = [sentences[0]]
        
        # Loop through each sentence in the list of sentences
        for sentence in sentences[1:]:
            # If the current sentence is not the same as the previous sentence, add it to the list of deduplicated sentences
            if sentence != deduplicated[-1]:
                deduplicated.append(sentence)
        
        # Join the deduplicated sentences into a string and return it
        return ".".join(deduplicated)

    def remove_noise(input_string, debug=False):

        onion = ''
        for sentence in sent_tokenize(input_string):
            
            if debug:
                print(sentence)
                print("------------------------------")
            
            # discard emails, prices, urls, bitcoin addresses
            if not find_onion_address(sentence) and not find_pgp_key(sentence) and not find_email_address(sentence) and not find_monetary_value(sentence) and not find_url(sentence) and not find_bitcoin_address(sentence) and not is_web_tag(sentence) and check_for_words:  # last preventive check for particular web-based keywords
                
                if debug:
                    print(sentence)
                    print("*********")
                
                sentence = remove_line_breaks_and_tabs(sentence)
                sentence = remove_special_characters(sentence)
                sentence = re.sub(' +', ' ', sentence)  # Replace multiple spaces with a single space
                sentence = remove_non_word_characters_at_beginning(sentence)
                sentence = remove_repeating_punctuation(sentence)
                sentence = remove_spaces_before_punctuation(sentence)
                sentence = deduplicate_words(sentence)

                if len(sentence) > 0 and sentence[-1] not in string.punctuation:
                    sentence = sentence+'.'

                sentence = sentence.strip()

                # Capitalize the first letter of each sentence
                sentence = re.sub(r'(^|[.!?])\s*([a-z])', lambda x: x.group(1) + ' ' + x.group(2).upper(), sentence)
                onion = "{0}{1} ".format(onion, sentence)
            
            else:
                if debug:
                    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                    print(sentence)
                    print(f"Words: {not check_for_words(sentence)}")
                    print(f"Onion: {find_onion_address(sentence)}")
                    print(f"PGP: {find_pgp_key(sentence)}")
                    print(f"Email: {find_email_address(sentence)}")
                    print(f"Monetary: {find_monetary_value(sentence)}")
                    print(f"URL: {find_url(sentence)}")
                    print(f"Bitcoin: {find_bitcoin_address(sentence)}")
                    print(f"Webtag: {is_web_tag(sentence)}")
                    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

        
        onion = modify_string(onion)
        onion = remove_repeating_punctuation(onion)
        onion = deduplicate_sentences(onion)
        return onion.strip()
    
    ponions = {}
    nempty_onions = 0
    ncleaned_onions = 0

    with open(cleaned_onions.path, 'rb') as f:
        onions = pickle.load(f)

    for address, text in onions.items():
        if text not in ['', 'bad encoded']:
            ncleaned_onions+=1
            cleaned_text = remove_noise(text)
            if cleaned_text == '':
                nempty_onions += 1
            ponions[address] = cleaned_text
        
        #if ncleaned_onions % 10 == 0:
        #    print(f"Preprocessed {ncleaned_onions}...")


    yesterday = date.today()- timedelta(days=1)
    fig = go.Figure(data=[go.Pie(labels=['Preprocessed onions', 'Empty onions (after preprocessing)'],
                                 values=[ncleaned_onions-nempty_onions, nempty_onions])])
    fig.update_layout(title=f'Preprocessed onions from {from_day}/{from_month}/{from_year} to {yesterday.day}/{yesterday.month}/{yesterday.year}')
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig))

    metrics.log_metric('Cleaned onions', ncleaned_onions)
    metrics.log_metric('Empty onions (after preprocessing)', nempty_onions)
    metrics.log_metric('Preprocessed onions', ncleaned_onions-nempty_onions)
    with open(preprocessed_onions.path, 'wb') as f:
        pickle.dump(ponions, f)


@dsl.component(
    base_image='python:3.9-alpine',
    packages_to_install = [
        "minio",
        "plotly"
    ]
)
def version_preprocessed_dataset(from_day:int, from_month:int, from_year:int, preprocessed_onions: Input[Artifact], metrics: Output[Metrics], plot: Output[HTML]):
    from minio import Minio
    import pickle
    from datetime import date, timedelta
    from minio.error import S3Error
    import io
    import plotly.graph_objs as go
    import plotly.io as pio

    client = Minio(
        endpoint="minio.minio:9000",
        secure=False,
        access_key='processing',
        secret_key=',TkTV3c7:e6#e}HwiD4R'
    )
    
    with open(preprocessed_onions.path, 'rb') as f:
        new_onions = pickle.load(f)


    # download last version
    first_version = date(2022, 11, 15)                      # threshold of first version
    last_date = date(from_year, from_month, from_day)        # dates to check from now to origin
    last_dataset = None                                     # indicates if previous version found
    
    while (last_date > first_version and last_dataset is None):
        last_date = last_date - timedelta(days=1)
        print("Checking version of", last_date.strftime("%d-%m-%Y"), "...")
        try:
            response = client.get_object("datasets",f"{last_date.year}/{last_date.month}/{last_date.day}/preprocessed_onions/preprocessed_onions.pickle")
            last_dataset = pickle.loads(response.read())
        except S3Error as exc:
            print("It does not exist! Next...", exc)
            continue

    # update to new version 
    if last_dataset is None:
        updated_dataset = new_onions
    else:
        last_dataset.update(new_onions)
        updated_dataset = last_dataset
    
    total_cleaned_onions = 0
    total_empty_onions = 0
    for onion, text in updated_dataset.items():
        total_cleaned_onions +=1
        if text == '':
            total_empty_onions+=1
        

    ##### write to MinIO
    versioning_date = date.today() - timedelta(days=1)

    bytes_file = pickle.dumps(updated_dataset)
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/preprocessed_onions/preprocessed_onions.pickle",
            data=io.BytesIO(bytes_file),
            length=len(bytes_file))
    
    stats = f"Total cleaned onions: {total_cleaned_onions}\nTotal empty onions: {total_empty_onions}\nTotal preprocessed onions: {total_cleaned_onions-total_empty_onions}"
    stats_bytes = stats.encode('utf-8')
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/preprocessed_onions/stats.txt",
            data=io.BytesIO(stats_bytes),
            length=len(stats_bytes))

    #### metrics and plot
    fig = go.Figure(data=[go.Pie(labels=['Total empty onions (after preprocessing)', 'Total preprocessed onions'],
                                 values=[total_empty_onions, total_cleaned_onions-total_empty_onions])])
    fig.update_layout(title=f'Total onions until {versioning_date.day}/{versioning_date.month}/{versioning_date.year}')
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig))

    metrics.log_metric('Total cleaned onions', total_cleaned_onions)
    metrics.log_metric('Total empty onions (after preprocessing)', total_empty_onions)
    metrics.log_metric('Total preprocessed onions', total_cleaned_onions-total_empty_onions)


# Define the language identification component
@dsl.component(
    base_image='python:3.8-slim',
    packages_to_install = [
        "numpy",
        "minio",
        "plotly",
        "datasketch"
    ]
)
def deduplicate_onions(from_day:int, from_month:int, from_year:int, preprocessed_onions: Input[Artifact], exactduplicated_onions: Output[Artifact], nearduplicated_onions: Output[Artifact], metrics: Output[Metrics], plot: Output[HTML]):
    from minio import Minio
    import pickle
    from datetime import date, timedelta
    from minio.error import S3Error
    import io
    import plotly.graph_objs as go
    import plotly.io as pio

    client = Minio(
        endpoint="minio.minio:9000",
        secure=False,
        access_key='processing',
        secret_key=',TkTV3c7:e6#e}HwiD4R'
    )
    
    with open(preprocessed_onions.path, 'rb') as f:
        new_onions = pickle.load(f)


    # download last version
    first_version = date(2022, 11, 15)          # threshold of first version
    last_date = date(from_year, from_month, from_day)                     # dates to check from now to origin
    exact_onions = None                    # indicates if previous version found
    while (last_date > first_version and exact_onions is None):
        last_date = last_date - timedelta(days=1)
        print("Checking version of", last_date.strftime("%d-%m-%Y"), "...")
        try:
            response = client.get_object("datasets",f"{last_date.year}/{last_date.month}/{last_date.day}/deduplicated_onions/exact_onions.pickle")
            exact_onions = pickle.loads(response.read())
        except S3Error as exc:
            print("It does not exist! Next...", exc)
            continue

    # calculate exact duplicates
    if exact_onions is None:
        exact_onions = {}
 
    total_onions = 0
    exact_duplicates = 0
    non_exact_duplicates = 0
    new_unique_onions = []
    for address,text in new_onions.items():
        if text != '':
            total_onions += 1
            result = exact_onions.get(text, False)
            if result is False:
                non_exact_duplicates += 1
                exact_onions[text] = [address]
                new_unique_onions.append(text)
            else:
                exact_onions[text].append(address)
                exact_duplicates += 1
            
    with open(exactduplicated_onions.path, 'wb') as f:
        pickle.dump(exact_onions, f)

    # calculate near duplicates

    from collections import defaultdict
    from datasketch import MinHash, MinHashLSH

    def union_of_intersecting_arrays(arr1, arr2):
        # Create a set from each array
        s1 = set(arr1)
        s2 = set(arr2)

        # Check if the sets intersect
        if s1.intersection(s2):
            # Return the union of the sets as a list
            return list(s1.union(s2))
        else:
            # If the sets do not intersect, return False
            return []

    def group_duplicate_texts_minhashlsh(texts):
            
        # Create a MinHash LSH index
        lsh = MinHashLSH(threshold=0.5, num_perm=128)

        # For each text in the list of texts, create a MinHash object and add it to the index
        for i,text in enumerate(texts):
            minhash = MinHash(num_perm=128)
            for word in text.split():
                minhash.update(word.encode('utf8'))
            lsh.insert(text, minhash)
        
        # For each text in the list of texts, find the groups of duplicates
        duplicate_groups = {}
        nduplicates=0
        for text in texts:
            minhash = MinHash(num_perm=128)
            for word in text.split():
                minhash.update(word.encode('utf8'))
            duplicates = lsh.query(minhash)
            
            found = False
            for duplicate_address, duplicate_group in duplicate_groups.items():
                union = union_of_intersecting_arrays(duplicates, duplicate_group)     # go through all the array, not only the first
                if union!=[]:
                    found = True
                    duplicate_groups[duplicate_address] = union
                    break
            
            if not found:
                duplicate_groups[text] = duplicates

        return duplicate_groups
    

    print(f"Deduplicating {len(exact_onions)} onions...")
    duplicates_minhash = group_duplicate_texts_minhashlsh(list(exact_onions.keys()))
    duplicates_minhash_2 = {}
    duplicated_onions = []
    for onion, duplicates in duplicates_minhash.items():
        
        for duplicate in duplicates:
            if duplicate not in duplicated_onions: 
                if duplicates_minhash_2.get(onion, False) is False:
                    duplicates_minhash_2[onion] = []
                duplicates_minhash_2[onion].append(duplicate)
                duplicated_onions.append(duplicate)
    
    duplicates_minhash = duplicates_minhash_2
    
    ## Count near duplicates and get the longer onion service as the representative one.
    final_unique_onions = 0
    near_duplic_onions = 0
    near_duplicates = {}


    for onion, near_duplicated_onions in duplicates_minhash.items():

        # get the representative onion
        representative_onion = onion
        for near_duplicated_onion in near_duplicated_onions:
            if len(near_duplicated_onion) > len(representative_onion):
                representative_onion = near_duplicated_onion
        near_duplicates[representative_onion] = near_duplicated_onions

        # check new unique and near-duplic onions
        for ndo in near_duplicates[representative_onion]:
            if ndo != representative_onion and ndo in new_unique_onions:
                near_duplic_onions += 1
            elif ndo == representative_onion and ndo in new_unique_onions:
                final_unique_onions += 1
            
    with open(nearduplicated_onions.path, 'wb') as f:
        pickle.dump(near_duplicates, f)
        
        
    #### metrics and plot
    yesterday = date.today() - timedelta(days=1)

    fig = go.Figure(data=[go.Pie(labels=['Exact mirrors', 'Near mirrors', 'Unique onions'],
                                 values=[exact_duplicates, near_duplic_onions, final_unique_onions])])
    fig.update_layout(title=f'Deduplicated onions from {from_day}/{from_month}/{from_year} to {yesterday.day}/{yesterday.month}/{yesterday.year}')
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig))

    metrics.log_metric('Total onions', total_onions)
    metrics.log_metric('Exact mirrors', exact_duplicates)
    metrics.log_metric('Near mirrors', near_duplic_onions)
    metrics.log_metric('Unique onions', final_unique_onions)




@dsl.component(
    base_image='python:3.8-slim',
    packages_to_install = [
        "minio",
        "plotly"
    ]
)
def version_deduplicated_dataset(from_day:int, from_month:int, from_year:int, exactduplicated_onions: Input[Artifact], nearduplicated_onions: Input[Artifact], metrics: Output[Metrics], plot: Output[HTML]):
    from minio import Minio
    import pickle
    from datetime import date, timedelta
    from minio.error import S3Error
    import io
    import plotly.graph_objs as go
    import plotly.io as pio

    client = Minio(
        endpoint="minio.minio:9000",
        secure=False,
        access_key='processing',
        secret_key=',TkTV3c7:e6#e}HwiD4R'
    )
    
    with open(exactduplicated_onions.path, 'rb') as f:
        exact_duplicated_onions = pickle.load(f)

    with open(nearduplicated_onions.path, 'rb') as f:
        near_duplicated_onions = pickle.load(f)


    ##### write to MinIO
    versioning_date = date.today() - timedelta(days=1)

    bytes_file = pickle.dumps(exact_duplicated_onions)
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/deduplicated_onions/exact_onions.pickle",
            data=io.BytesIO(bytes_file),
            length=len(bytes_file))
    
    bytes_file = pickle.dumps(near_duplicated_onions)
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/deduplicated_onions/near_onions.pickle",
            data=io.BytesIO(bytes_file),
            length=len(bytes_file))
    
    bytes_file = pickle.dumps(list(near_duplicated_onions.keys()))
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/deduplicated_onions/unique_onions.pickle",
            data=io.BytesIO(bytes_file),
            length=len(bytes_file))
    

    ### stats

    total_onions = 0
    exact_duplicates = 0
    instances = {}
    for text, addresses in exact_duplicated_onions.items():
        exact_duplicates += len(addresses)-1
        total_onions += len(addresses)-1

    near_duplicates = 0
    for text, near_texts in near_duplicated_onions.items():
        near_duplicates += len(near_texts)-1
        total_onions += len(near_texts)
        instances[text] = len(near_texts)
        instances[text] += len(exact_duplicated_onions[text])-1

    final_unique_onions = len(near_duplicated_onions.keys())

    stats = f"Preprocessed onions: {total_onions}\nExact mirrors: {exact_duplicates}\nNear mirrors: {near_duplicates}\nUnique onions: {final_unique_onions}"
    stats_bytes = stats.encode('utf-8')
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/deduplicated_onions/stats.txt",
            data=io.BytesIO(stats_bytes),
            length=len(stats_bytes))


    #### metrics and plot
    fig = go.Figure(data=[go.Pie(labels=['Total exact mirrors', 'Total near mirrors', 'Total unique onions'],
                                 values=[exact_duplicates, near_duplicates, final_unique_onions])])
    fig.update_layout(title=f'Total duplicated onions until {versioning_date.day}/{versioning_date.month}/{versioning_date.year}')

    #### save the boxplot distribution of instances in html boxplot variable
    fig2 = go.Figure(data=[go.Box(y=list(instances.values()), boxpoints=False)])
    fig2.update_layout(title=f'Boxplot of instances of each onion until {versioning_date.day}/{versioning_date.month}/{versioning_date.year}')
    
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig)+pio.to_html(fig2))

    metrics.log_metric('Total onions', total_onions)
    metrics.log_metric('Total exact mirrors', exact_duplicates)
    metrics.log_metric('Total near mirrors', near_duplicates)
    metrics.log_metric('Total unique onions', final_unique_onions)



# Define the language identification component
@dsl.component(
    base_image='python:3.8',
    packages_to_install = [
        "minio",
        "fasttext",
        "pycountry",
        "pandas",
        "plotly"
    ]
)
def identify_languages(unique_onions: Input[Artifact], language_output: Output[Artifact], plot: Output[HTML], metrics: Output[Metrics]):
    import fasttext
    from pycountry import languages
    from datetime import date, timedelta
    import pickle

    class LanguageIdentification:

        def __init__(self):
            # connect to MinIO and download the model
            from minio import Minio
            import io
            client = Minio(
                endpoint="minio.minio:9000",
                secure=False,
                access_key='processing',
                secret_key=',TkTV3c7:e6#e}HwiD4R')
           
            try:
                client.fget_object(bucket_name='models', object_name='language/lid.176.bin', file_path='/tmp/lid.176.bin')
            except:
                print("Error downloading the model")
            
            pretrained_lang_model = '/tmp/lid.176.bin'
            self.model = fasttext.load_model(pretrained_lang_model)

        def predict_lang(self, text):
            predictions = self.model.predict(text, k=2) # returns top 2 matching languages
            return predictions

    def get_languages(text):

        LANGUAGE = LanguageIdentification()
        
        lang = LANGUAGE.predict_lang(text)

        ### language distribution
        first_language, second_language = None, None
        try:
            first_language = languages.get(alpha_2=lang[0][0].split("__label__")[1]).name
        except:
            first_language = lang[0][0].split("__label__")[1]

        first_confidence = lang[1][0]
        
        try:
            second_language = languages.get(alpha_2=lang[0][1].split("__label__")[1]).name
        except:
            second_language = lang[0][1].split("__label__")[1]

        second_confidence = lang[1][1]
        
        return first_language, first_confidence, second_language, second_confidence


    # read pickle file with unique onions
    with open(unique_onions.path, 'rb') as f:
        onions = pickle.load(f)
    
    dict_lang = {'first_language': [],
                'first_confidence': [],
                'second_language': [],
                'second_confidence': []}
    
    onion_languages = {}


    for onion in list(onions.keys()):
        first_language, first_confidence, second_language, second_confidence = get_languages(onion)
        dict_lang['first_language'].append(first_language)  
        dict_lang['first_confidence'].append(first_confidence)
        dict_lang['second_language'].append(second_language)  
        dict_lang['second_confidence'].append(second_confidence)
        
        onion_languages[onion] = {}
        onion_languages[onion]['first_language'] = first_language 
        onion_languages[onion]['first_confidence'] = first_confidence
        onion_languages[onion]['second_language'] = second_language
        onion_languages[onion]['second_confidence'] = second_confidence
    
    
    # write a pie chart in plot argument with the distribution of first language of the onions which is in 'first_language' list of dict_lang
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.io as pio

    df = pd.DataFrame(dict_lang)
    df = df.first_language.value_counts()/len(df)*100
    df = df.reset_index()
    df.columns = ['language', 'percentage']
    df = df.sort_values(by='percentage', ascending=False)
    df = df.head(10)
    fig = go.Figure(data=[go.Pie(labels=df.language, values=df.percentage)])

    versioning_date = date.today() - timedelta(days=1)
    fig.update_layout(title=f'Language distribution of onions until {versioning_date.day}/{versioning_date.month}/{versioning_date.year}')
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig))


    # write the onion_languages dictionary in the language_output artifact as a pickle
    with open(language_output.path, 'wb') as f:
        pickle.dump(onion_languages, f)

    # write in metrics the number of onions per language
    metrics.log_metric('Total onions', len(onion_languages))
    for language in df.language:
        metrics.log_metric(language, df[df.language == language].percentage.values[0])


@dsl.component(
    base_image='python:3.8-slim',
    packages_to_install = [
        "minio",
        "plotly",
        "pandas"
    ]
)
def version_language_dataset(from_day:int, from_month:int, from_year:int, language_input: Input[Artifact], plot: Output[HTML], metrics: Output[Metrics]):

    # get from MinIO the onion_languages dictionary of previous version
    from minio import Minio
    from minio import S3Error
    import pickle
    from datetime import date, timedelta
    
    client = Minio(
        endpoint="minio.minio:9000",
        secure=False,
        access_key='processing',
        secret_key=',TkTV3c7:e6#e}HwiD4R')
    

    with open(language_input.path, 'rb') as f:
        onion_languages = pickle.load(f)

    # download last version
    first_version = date(2022, 11, 15)                      # threshold of first version
    last_date = date(from_year, from_month, from_day)        # dates to check from now to origin
    last_dataset = None                                     # indicates if previous version found
 
    while (last_date > first_version and last_dataset is None):
        last_date = last_date - timedelta(days=1)
        print("Checking version of", last_date.strftime("%d-%m-%Y"), "...")
        try:
            response = client.get_object("datasets",f"{last_date.year}/{last_date.month}/{last_date.day}/languages/languages.pickle")
            last_dataset = pickle.loads(response.read())
        except S3Error as exc:
            print("It does not exist! Next...", exc)
            continue

    # update to new version 
    if last_dataset is None:
        updated_dataset = onion_languages
    else:
        last_dataset.update(onion_languages)
        updated_dataset = last_dataset
    
    ##### write to MinIO
    import io
    
    versioning_date = date.today() - timedelta(days=1)
    bytes_file = pickle.dumps(updated_dataset)
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/languages/languages.pickle",
            data=io.BytesIO(bytes_file),
            length=len(bytes_file))

    # plot the distribution of languages of the first language in onion_languages[onion]['first_language']
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.io as pio

    df = pd.DataFrame(updated_dataset).T
    df = df.first_language.value_counts()/len(df)*100
    df = df.reset_index()
    df.columns = ['language', 'percentage']
    df = df.sort_values(by='percentage', ascending=False)
    df = df.head(10)
    fig = go.Figure(data=[go.Pie(labels=df.language, values=df.percentage)])
    fig.update_layout(title=f'Language distribution of onions until {versioning_date.day}/{versioning_date.month}/{versioning_date.year}')
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig))
    

    ## write to MinIO the stats of the first 10 languages in text file
    import io
    stats = df.to_string(index=False)
    client.put_object(
            bucket_name="datasets",
            object_name=f"{versioning_date.year}/{versioning_date.month}/{versioning_date.day}/languages/stats.txt",
            data=io.BytesIO(stats.encode()),
            length=len(stats))


    # write in metrics the number of onions per language
    metrics.log_metric('Total onions', len(updated_dataset))
    for language in df.language:
        metrics.log_metric(language, df[df.language == language].percentage.values[0])
    

# Define the text classification component
@dsl.component(
    base_image='python:3.8-slim',
    packages_to_install = [
        "nltk",
        "plotly",
        "pandas",
        "bertopic==0.14.0",
        "minio",
        "stopwordsiso"
    ]    
)
def classify_onions(from_day:int, from_month:int, from_year:int, language_output: Input[Artifact], metrics: Output[Metrics], plot: Output[HTML]):
    
    # Get the list of onions with first language is English
    import pickle
    with open(language_output.path, 'rb') as f:
        onion_languages = pickle.load(f)
    onion_list = [onion for onion in onion_languages if onion_languages[onion]['first_language'] == 'English']


    # Get the distribution of number of words and number of sentences in the onion_list to write in plot
    import nltk
    nltk.download('punkt')
    from nltk.tokenize import sent_tokenize, word_tokenize
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import plotly.io as pio

    onion_sentences = []
    onion_words = []
    for onion in onion_list:
        onion_sentences.append(len(sent_tokenize(onion)))
        onion_words.append(len(word_tokenize(onion)))
    
    df = pd.DataFrame({'onion_sentences': onion_sentences, 'onion_words': onion_words})
    df2 = df.groupby('onion_sentences').count().reset_index()
    df2.columns = ['onion_sentences', 'count']
    #fig = go.Figure(data=[go.Bar(x=df.onion_sentences, y=df.count)])
    fig = go.Figure(data=[go.Box(y=df2.onion_sentences, boxpoints='all', jitter=0.3, pointpos=-1.8)])
    fig.update_layout(title=f'Number of sentences per onion until {from_day}/{from_month}/{from_year}')
    
    df3 = df.groupby('onion_words').count().reset_index()
    df3.columns = ['onion_words', 'count']
    fig2 = go.Figure(data=[go.Box(y=df3.onion_words, boxpoints='all', jitter=0.3, pointpos=-1.8)])
    fig2.update_layout(title=f'Number of words per onion until {from_day}/{from_month}/{from_year}')
    
    with open(plot.path, 'w') as p:
        p.write(pio.to_html(fig)+pio.to_html(fig2))



# Define the pipeline
@dsl.pipeline(
    name="onion-analysis-pipeline"
)
def onion_analysis_pipeline(from_day: int, from_month: int, from_year: int) -> None:
    # download, clean, and version
    download_step = download_onions(from_day,from_month,from_year)
    version_onion_dataset(from_day,from_month,from_year,download_step.outputs['cleaned_onions'])
    
    # preprocess and version
    preprocess_step = preprocess_onions(from_day,from_month,from_year,download_step.outputs['cleaned_onions'])
    version_preprocessed_dataset(from_day,from_month,from_year,preprocess_step.outputs['preprocessed_onions'])
    
    # deduplicate
    deduplicate_step = deduplicate_onions(from_day,from_month,from_year,preprocess_step.outputs['preprocessed_onions'])
    version_deduplicated_dataset(from_day,from_month,from_year,deduplicate_step.outputs['exactduplicated_onions'],deduplicate_step.outputs['nearduplicated_onions'])

    # language identification
    language_step = identify_languages(deduplicate_step.outputs['nearduplicated_onions'])
    version_language_dataset(from_day,from_month,from_year,language_step.outputs['language_output'])

    classify_step = classify_onions(from_day,from_month,from_year,language_step.outputs['language_output'])
    


# Compile the pipeline
pipeline_func = onion_analysis_pipeline
pipeline_filename = pipeline_func.__name__ + ".yaml"
kfp.compiler.Compiler(mode=kfp.dsl.PipelineExecutionMode.V2_COMPATIBLE).compile(pipeline_func, pipeline_filename)

# Submit the pipeline
client = kfp.Client(host="http://localhost:8880")

experiment_name = f"Onion analysis"
today = date.today()
yesterday = today - timedelta(days=1)
from_day, from_month, from_year = yesterday.day, yesterday.month, yesterday.year
# from_day, from_month, from_year = 14, 11, 2022
run_name = f"Onions collected from {from_day}/{from_month}/{from_year} to {yesterday.day}/{yesterday.month}/{yesterday.year}"

run_result = client.create_run_from_pipeline_func(
    pipeline_func,
    mode=kfp.dsl.PipelineExecutionMode.V2_COMPATIBLE,
    experiment_name=experiment_name,
    run_name=run_name,
    arguments={
        "from_day": from_day,
        "from_month": from_month, 
        "from_year": from_year, 
    }
    )
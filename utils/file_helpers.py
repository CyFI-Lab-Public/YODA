import re
import os
import subprocess
import hashlib # testing

def read_file(file_path):
    """ Read file and attempts to decode it in multiple ways
    """
    content_bytes = None
    with open(file_path, 'rb') as file_handler:
        content_bytes = file_handler.read()

    content = decode(content_bytes)
    return content
    
def decode(content_bytes):
    """ Returns a string of file contents
    Tries utf-8, ascii and latin encodings
    """

    content = None
    utf_worked = True
    ascii_worked = True
    latin_worked = True
    # Try all the popular encodings
    try:
        content = content_bytes.decode('utf-8')
    except UnicodeDecodeError as e:
        utf_worked = False 

    if not utf_worked:
        try:
            content = content_bytes.decode('ascii')
        except UnicodeDecodeError as e:
            ascii_worked = False

    if not utf_worked or not ascii_worked:
        try:
            content = content_bytes.decode('latin_1')
        except UnicodeDecodeError as e:
            latin_worked = False

    if utf_worked or ascii_worked or latin_worked: 
        return content
    else:
        raise UnicodeDecodeError

def normalize_file_content(content):
    """Removes php comments, tabs, multiple spaces and return lines

    content: file contents as string
    returns: normalized file contents as string
    """
    # Remove php comments
    # replace multiline comments that are preceded by <?php with a space rather
    # than nothing
    content = re.sub(re.compile('/\*.*?\*/', re.DOTALL) , ' ', content)
    content = re.sub(re.compile('//.*?\n' ), '', content)
    # Normalize string data
    # replace newlines with '' when they do not immediately follow <?php
    # this should match all possible line endings
    content = re.sub(re.compile('(?<!\<\?php)(\r\n|\r|\n)'), '', content) 
    # merge whitespace
    content = re.sub('\s+', ' ', content)
    return content

def bad_normalize_file_content(filepath):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    get_ast_php_path = os.path.join(script_dir, './get_ast.php')
    abspath = os.path.abspath(filepath)

    try: 
        output = subprocess.check_output([
                'php',
                get_ast_php_path,
                abspath
            ],
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError:
        # non-zero exit code
        return None

    # no exception, was successful
    return output

def add_tags(filepath):
    """prepends '<?php' and appends '?>' to file if it doesn't start with '<?php'
    returns true if it added any tags"""
    did_add_tags = False

    # Read file
    file_text = read_file(filepath)
    # Add tags to file contents
    new_text = add_tags_to_file_text(file_text)
    # Write new contents to file
    with open(filepath, 'w') as f:
        f.write(new_text)

    return file_text == new_text

def add_tags_to_file_bytes(file_bytes):
    """prepends '<?php' and appends '?>' to file contents (BYTES) if it doesn't start with '<?php'
    returns STRING containing the tags"""
    file_text = decode(file_bytes)
    return add_tags_to_file_text(file_text)

def add_tags_to_file_text(file_text):
    """prepends '<?php' and appends '?>' to file contents if it doesn't start with '<?php' """
    file_text
    # check the first 5 chars, if they aren't <?php, add <?php
    if len(file_text) >= 5:
        # don't support this case yet
        """if file_text[0:2] == '<?' and file_text[0:5] != '<?php':
            new_text = '<?php\n' + file_text[2:] + '\n?>'
        """

        if file_text[0:5] != '<?php':
            file_text = '<?php\n' + file_text + '\n?>'

    return file_text

def create_word_blocks(document):
    """ Takes a document string and blocks it into words for NLP
    Current implementation blocks by ';'
    """
    return document.split(' ')

def hash_file_contents(file_contents):
    file_contents = normalize_file_content(file_contents)
    return hashlib.md5(file_contents.encode()).hexdigest()

if __name__ == '__main__':
    #norm1 = normalize_file_content('./test.php')
    #norm2 = normalize_file_content('./test1.php')

    norm1 = normalize_file_content('/mnt/data/first_85_websites/Repos/website-682886/www.joncomet.com/web/content/includes/mail.inc')
    norm2 = normalize_file_content('/home/eric/cms-malware-forensics/analysis/mailer_detection/whitelist/drupal/drupal-mail.php')

    with open('norm1.php', 'wb') as f1:
        f1.write(norm1)

    with open('norm2.php', 'wb') as f2:
        f2.write(norm2)
    #print(norm1)
    #print(norm2)

    print(hashlib.md5(norm1).hexdigest())
    print(hashlib.md5(norm2).hexdigest())

    assert (norm1 == norm2), 'content should be equal'

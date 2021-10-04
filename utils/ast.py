import json
import os
import subprocess
import sys

def get_ast(filepath):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    get_ast_php_path = os.path.join(script_dir, '../php_metrics/get_ast.php')
    abspath = os.path.abspath(filepath)

    try: 
        output = subprocess.check_output([
                'php',
                get_ast_php_path,
                abspath
            ],
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        # non-zero exit code
        print(e)
        return None

    # no exception, was successful
    return json.loads(output.decode('utf-8'))
    #return __remove_attrs(output)

def pretty_print(filepath, remove_try_catch=False):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    pretty_print_php_path = os.path.join(script_dir, '../php_metrics/pretty_print.php')
    abspath = os.path.abspath(filepath)

    try: 
        args = [
                'php',
                pretty_print_php_path,
                abspath,
               ]

        if remove_try_catch:
            args.append('-r')
        print(args)
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # non-zero exit code
        print(e)
        return None

    # no exception, was successful
    return output.decode('utf-8')


def __remove_attrs(parser_output):
    try:
        ast_dict = json.loads(parser_output.decode('utf-8'))
        __remove_attrs_helper(ast_dict)
        return json.dumps(ast_dict)
    except:
        return None

def __remove_attrs_helper(ast_dict):
    remove_me = 'attributes'
    if isinstance(ast_dict, dict):
        if remove_me in ast_dict:
            del ast_dict[remove_me]

        for k, v in ast_dict.items():
            if isinstance(v, dict):
                __remove_attrs_helper(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        __remove_attrs_helper(item)

    elif isinstance(ast_dict, list):
        for item in ast_dict:
            if isinstance(item, dict):
                __remove_attrs_helper(item)

if __name__ == '__main__':
    #print(get_ast('./test.php'))
    print(get_ast(sys.argv[1]))

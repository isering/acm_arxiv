 #! /usr/bin/env python
"""
Author: Julian Iseringhausen <iseringhausen@cs.uni-bonn.de>
Year: 2019

This script can be used to prepare a submission for arXiv. The script expects the main LaTex file to be main.tex. The LaTex document has to be compiled before.

The main.tex file has to start with (before \documentclass):
\RequirePackage{snapshot}

For some reason this latexpand does not like to be called from bash under Windows. Call from cmd in case of errors.

Requirements:
latexpand
"""

import argparse
import os
import re
import shutil
import subprocess
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--out', default='arxiv', help='Output folder containing the stripped LaTex project (default: arxiv)')
parser.add_argument('--zip', default='arxiv.zip', help='Output zip file (default: arxiv.zip)')
parser.add_argument('--collapse_empty', dest='collapse_empty', action='store_true')
parser.add_argument('--no-collapse_empty', dest='collapse_empty', action='store_false')
parser.set_defaults(collapse_empty=False)
parser.add_argument('filename', help='Main LaTex file')
args = parser.parse_args()

replace_strings = [['\\documentclass', '\\documentclass[acmtog, authorversion]{acmartarxiv}\n'],
                   ['\\setcopyright', '\\settopmatter{printacmref=false,printccs=false}\n\\fancyfoot{}\n\\setcopyright{rightsretained}\n'],
                   ['\\maketitle', '\\maketitle\n\\thispagestyle{empty}\n']]
dependency_extensions = ['pdf', 'png', 'jpg', 'jpeg']
commands_to_remove = ['\\acmSubmissionID', '\\acmJournal', '\\acmVolume', '\\acmNumber',
                      '\\acmArticle', '\\acmYear', '\\acmMonth', '\\acmDOI',
                      '\\received', '\\RequirePackage']
tex_files_to_copy_optional = [os.path.splitext(args.filename)[0] + '.ind',
                              os.path.splitext(args.filename)[0] + '.gls']
tex_files_to_copy_required = ['acmartarxiv.cls', 'ACM-Reference-Format.bst']


def check_file(filename):
    if not os.path.exists(filename):
        print('Required file not found: {}'.format(filename))
        exit()


def copy_file(filename, optional=True):
    if os.path.exists(filename):
        dir_out = os.path.join(args.out, os.path.dirname(filename))
        if not os.path.exists(dir_out):
            os.makedirs(dir_out)
        shutil.copy(filename, dir_out)
    elif not optional:
        print('Required file not found: {}'.format(filename))
        exit()


def is_comment_line(line):
    return line.lstrip().startswith('%')


def replace_line(lines, line_contains, replace_str):
    for i, line in enumerate(lines):
        if line_contains in line:
            lines[i] = replace_str
            break


def main():
    # Get filenames and check whether the required files exist.
    bbl_file = os.path.splitext(args.filename)[0] + '.bbl'
    dep_file = os.path.splitext(args.filename)[0] + '.dep'
    for filename in [args.filename, bbl_file, dep_file]:
        check_file(filename)

    # Remove old files.
    if os.path.exists(args.out):
        shutil.rmtree(args.out)
    if os.path.exists(args.zip):
        os.remove(args.zip)
    
    # Create output directory if it does not already exist.
    if not os.path.exists(args.out):
            os.makedirs(args.out)

    # Merge TeX files and remove comments.
    with open(os.path.join(args.out, args.filename), 'w') as f:
        subprocess.call(['latexpand', '--empty-comments', '--expand-bbl', bbl_file, args.filename], stdout=f)
        
    # Modify main LaTex file.
    main_content = ''
    with open(os.path.join(args.out, args.filename), 'r') as f:
        lines = f.readlines()
        
        # Replace documentclass and copyright.
        for replace_string in replace_strings:
            replace_line(lines, replace_string[0], replace_string[1])

        # Remove remaining empty comment lines.
        for line in lines:
            if not is_comment_line(line) and not any(str in line for str in commands_to_remove):
                main_content += line
                
    # Remove subsequent empty lines.
    if args.collapse_empty:
        main_content = re.sub(r'\n\s*\n', '\n\n', main_content)

    # Write modified main LaTex file.
    with open(os.path.join(args.out, args.filename), 'w') as f:
        f.write(main_content)
                
    # Copy dependencies.
    with open(dep_file, 'r') as f:
        for line in f:
            if not '*{file}' in line:
                continue
            filename_dep = line.split('{')[2].split('}')[0]
            _, ext = os.path.splitext(filename_dep)
            if not ext.lower()[1:] in dependency_extensions:
                continue
            copy_file(filename_dep, optional=False)

    # Copy remaining files.
    for filename in tex_files_to_copy_optional:
        copy_file(filename, optional=True)
    for filename in tex_files_to_copy_required:
        copy_file(filename, optional=False)

    # Create zip file for uploading to ArXiv.
    with zipfile.ZipFile(args.zip, 'w', zipfile.ZIP_DEFLATED) as zip_handle:
        cwd_old = os.getcwd()
        os.chdir(args.out)
        for root, _, files in os.walk('.'):
            for file in files:
                zip_handle.write(os.path.join(root, file))
        os.chdir(cwd_old)

if __name__ == '__main__':
    main()
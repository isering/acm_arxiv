# acm_arxiv
This is a primitive script to convert my ACM submissions to ArXiv. For anybody else, it probably has to be modified.

## How to
The main tex file has to start with `\RequirePackage{snapshot}` before `\documentclass` and has to be fully compiled before running the `prepare_arxiv.py` script. The LaTex project should use the `ACM-Reference-Format`.

## Requirements
* latexpand

## Features
* Collapse input tex files into a single file
* Remove comments
* Collapse subsequent empty lines
* Replace documentclass and copyright
* Find and copy dependencies and image files
* Zip files for convenient upload

import os
import argparse
import mmap
import yaml

description = "Update the LaTeX documentation with the current .yml file content.  Run this script before building" + \
              " the LaTeX documentation for the most up-to-date documentation.  This must be run with Python 2."

parser = argparse.ArgumentParser(description=description)
parser.add_argument('ymlpath', type=str, help="Path to the Directory.yml file.")
parser.add_argument('--card', type=str, default='cards.tex', help="Path to the cards.tex file.  Assumes this script is being run from its directory if not provided.")
args = parser.parse_args()

if not os.path.exists(args.ymlpath):
    raise RuntimeError("Path to Directory.yml file does not exist: " + str(args.ymlpath))

fin = args.ymlpath
fout = args.card
err_count = 0
content_found = 0

blocks = []
build_tex = True
with open(fin, 'r') as f:
    code = yaml.safe_load(f)
    for name, val in code['_DIRECTORY'].items():
        blocks.append(name)
    for block in blocks:
        for name, val in code[block].items():
            if name[0] != "_":
                with open(fin, 'r') as f:
                    s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                    if "_" in name:
                        mod_name = name.replace("_", "\_")
                        if s.find(b"bf " + mod_name.encode()) != -1:
                            content_found = content_found + 1
                        else:
                            err_count += 1
                            print('There was content missing from the ' + name + ' in section ' + block)
                            build_tex = False
    check = os.environ.get('ENABLE_BUILD_TEX')
    if build_tex or check == "idkfa":
        print('starting to build tex file')
        with open(fout, 'w') as f:
            for line in open(fin):
                line = line.rstrip('\n').lstrip()
                if line.startswith("#>"):
                    dstr = line[2:]
                    f.write(dstr + "\n")
    else:
        print('There were ' + str(err_count) + ' instances of missing content, please see output for specific information. No TeX file(s) will be generated.')

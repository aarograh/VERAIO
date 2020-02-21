import os
import sys
import yaml
import mmap

#fin needs to be .yml file
fin   = sys.argv[1]
fout  = sys.argv[2]
err_count=0
content_found=0

blocks=[]
build_tex = "True"
with open(fin) as f:
  code = yaml.safe_load(f)
  for name,val in code['_DIRECTORY'].items():
    blocks.append(name)
  for block in blocks:
    for name,val in code[block].items():
       if name[0]!="_":
         f = open(fin)
         s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
         if "_" in name:
           mod_name=name.replace("_","\_")
           if s.find("bf "+mod_name) != -1:
               content_found=content_found+1
           else:
               err_count +=1
               print('There was content missing from the '+name+' in section '+block)
               build_tex = "False"
  check=os.environ.get('ENABLE_BUILD_TEX')
  if build_tex == "True" or check == "idkfa":
    print('starting to build tex file')
    f=open(fout,'w')
    for line in open(fin):
      line=line.rstrip('\n').lstrip()
      if(line.startswith("#>")):
           dstr=line[2:]
           f.write(dstr+"\n")
    f.close()
  else:
    print('There were '+format(err_count)+' instances of missing content, please see output for specific information. No TeX file(s) will be generated.')


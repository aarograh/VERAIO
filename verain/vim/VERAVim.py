################################################################################
# Acknowledgement that Srdjan Simunovic wrote most if not all of the PERL code
# in the VERAIO Repo, without his efforts this wrapper would not be possible.
#
# VERAIn is an open source PERL parser for the common input for CASL codes. It
# is found here - "VERA common input processor" https://github.com/CASL/VERAin
#
# This python file will read in the scripts/Templates .yml files from VERAIn and
# will create a python file that contains all of the data into python classes.
#
# Read the directory.yml file first, since it contains all of the blocks.
#
# Object decription:
# VERAIn Dictionary
# Contains:
#   A list of names block objects
#   each block object contains a list of card objects
#   each card object has an ascii name (singular), an xml name(s) (1 or more
#     outputs), a data type, associated error checks (0 or more).
#
# visually:
#   1-D list of blocks - Block1
#                        1-D list of cards - Card1
#                                            - Ascii name
#                                            - xml name
#                                            - data type
#                                            1-D list of error checks
#                                            ...
#                                            CardN
#                        ...
#                        BlockN
#
# Recommend doing scalars first, then arrays since the error checking import
# will be more complicated.
#
# Author: Daniel Jabaay, University of Michigan
# Date: 01/22/2018
#
# TODO:
#  1) Implement code to import the VERAIn common input .yml files into python
#  2) Implement code to read a VERA ascii file
#  3) Implement error checking
#  4) Implement writing to XML
#  5) Add other non-VERA code blocks to allow for multiple input generation.
#
################################################################################

import os
import sys
import VERADATATYPE as VDT
import VERABLOCK as VB
#import VERACARD as VC

class VERAIO:
  'A class to encapsulate the PERL .yml files from VERAIn'

  def __init__(self, pathToDir):
    self.isinit = False
    self.nBlocks = 0
    self.blocknames = []
    self.blocks = {}
    self.nDatatypes = 0
    self.datatypenames = []
    self.datatypes = {}

    #Get the path to the Directory.yml file, use that to get the blocks
    vindir = os.path.dirname(pathToDir)
    vindiryml = os.path.basename(pathToDir)
    #if it's a file like we expect, open it
    if os.path.isfile(pathToDir):
      diryml = open(pathToDir,'r')
      dirlines = diryml.readlines()
      diryml.close()

      #initialize the datatypes
      istt,istp = findBounds(dirlines,'_DATATYPES:','')
      self.datatypenames = findNames(dirlines[istt:istp],'&')
      blockind = findDTInd(dirlines[istt:istp],self.datatypenames,istt)
      #print('datatype blockind=',blockind)

      i=0
      for dt in self.datatypenames:
        self.datatypes[dt] = VDT.DATATYPE(dt,dirlines[blockind[i]:blockind[i+1]-1])
        i += 1
      self.nDataTypes = i

      #initialize the blocks and subsequent cards
      istt,istp = findBounds(dirlines,'_DIRECTORY:','')
      #Since the block names here are not necessarily in the same order in the file,
      #Store to a temp variable
      tmpblocknames = findNames(dirlines[istt:istp],'')
      #Return the actual block line indices and corresponding blockname for all of the
      #cards
      blockind, self.blocknames= findVINBlockInd(dirlines[istp+1:],tmpblocknames,istp+1)
      #print('block blockind=',blockind)
      #print('block blocknames=',self.blocknames)

      i=0
      for block in self.blocknames:
        #print(i,block)
        self.blocks[block] = VB.BLOCK(block,dirlines[blockind[i]:blockind[i+1]-1],self.datatypes)
        i += 1
      self.nBlocks = i

      self.isinit = True
      #mpact = self.getBlock('MPACT')
      #mpact.edit()
      #print(self.blocks)
      #self.edit()
      self.createVimSyntax()

  def edit(self):
    print('Class name =','VERAIO')
    print('nDatatypes =',self.nDatatypes)
    print('datatypenames =',self.datatypenames)
    for k, v in self.datatypes.items():
      v.edit()
    print('nBlocks =',self.nBlocks)
    print('blocknames =',self.blocknames)
    for k, v in self.blocks.items():
      v.edit()

  def isBlock(self,name):
    return name in self.blocknames

  def isCardinBlock(self,bname,cname):
    return cname in self.blocks[bname].cardnames

  def createVimSyntax(self):
    with open('syntax/verainput.vim','w') as f:
      f.write('"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++!\n')
      f.write('"                              Copyright (C) 2018                              !\n')
      f.write('"                   The Regents of the University of Michigan                  !\n')
      f.write('"              MPACT Development Group and Prof. Thomas J. Downar              !\n')
      f.write('"                             All rights reserved.                             !\n')
      f.write('"                                                                              !\n')
      f.write('" Copyright is reserved to the University of Michigan for purposes of          !\n')
      f.write('" controlled dissemination, commercialization through formal licensing, or     !\n')
      f.write('" other disposition. The University of Michigan nor any of their employees,    !\n')
      f.write('" makes any warranty, express or implied, or assumes any liability or          !\n')
      f.write('" responsibility for the accuracy, completeness, or usefulness of any          !\n')
      f.write('" information, apparatus, product, or process disclosed, or represents that    !\n')
      f.write('" its use would not infringe privately owned rights. Reference herein to any   !\n')
      f.write('" specific commercial products, process, or service by trade name, trademark,  !\n')
      f.write('" manufacturer, or otherwise, does not necessarily constitute or imply its     !\n')
      f.write('" endorsement, recommendation, or favoring by the University of Michigan.      !\n')
      f.write('"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++!\n')
      f.write('"\n')
      f.write('" Vim syntax file for VERA input files.\n')
      f.write('" Language: VERA Input file\n')
      f.write('" Maintainer: Dan Jabaay\n')
      f.write('" Latest Revision: 9/24/2019\n')
      f.write('"\n')
      f.write('" Reads the Directory.yml from the VERAIn repository and adds the block names\n')
      f.write('" and card names to the syntax highlighting for filetype verainput.\n')
      f.write('"\n')
      f.write('" This syntax file needs to be used in conjunction with the scripts.vim file\n')
      f.write('" to determine if a *.inp file is also of filetype verainput.\n')
      #f.write('"\n')
      #f.write('" Read and store data from the Directory.yml file in a dictionary\n')
      #f.write('" VERAIN->Blocks = list of block names\n')
      #f.write('"       -><Block_1>->cards = list of card names\n')
      #f.write('"                  -><card_1>->attributes = list of card attributes\n')
      #f.write('"                            ->arguments = list of card arguments\n')
      f.write("\n")
      f.write('if exists("b:current_syntax")\n')
      f.write('  finish\n')
      f.write('endif\n')
      f.write("\n")
      f.write('" comments, TODO\'s , and quotes\n')
      f.write('syn match   veraComment "!.*$" contains=veraTodo,@Spell\n')
      f.write('syn keyword veraTodo FIXME NOTE TODO XXX contained\n')
      f.write('syn region  veraString matchgroup=veraQuotes\n')
      f.write('      \ start=+[uU]\=\z([\'"]\)+ end="\z1" skip="\\\\\|\\\z1"\n')
      f.write('      \ contains=veraEscape,@Spell\n')
      f.write("\n")
      f.write('" Atomic Isotopes \n')
      f.write('syn match veraIsotope "\s[A-Za-z]{1,2}\-[0-9]{1,3}"\n')
      f.write('syn match veraIsotope "\s[0-9]{4,5}"\n')
      f.write("\n")
      f.write('" Integer with - + or nothing in front\n')
      f.write('syn match veraInt "\s\d\+"\n')
      f.write('syn match veraInt "\s[-+]\d\+"\n')
      f.write("\n")
      f.write('" Floating point number with decimal no E or e \n')
      f.write('syn match veraFloat "\s\d\+\.\d*"\n')
      f.write('syn match veraFloat "\s[-+]\d\+\.\d*"\n')
      f.write("\n")
      f.write('" Floating point like number with E and no decimal point (+,-)\n')
      f.write('syn match veraFloat "\s[-+]\=\d[[:digit:]]*[eE][\-+]\=\d\+"\n')
      f.write('syn match veraFloat "\s\d[[:digit:]]*[eE][\-+]\=\d\+"\n')
      f.write("\n")
      f.write('" Floating point like number with E and decimal point (+,-)\n')
      f.write('syn match veraFloat "\s[-+]\=\d[[:digit:]]*\.\d*[eE][\-+]\=\d\+"\n')
      f.write('syn match veraFloat "\s\d[[:digit:]]*\.\d*[eE][\-+]\=\d\+"\n')
      f.write("\n")
      f.write('" detects numbers\n')
      f.write('"syn match   veraNumber  "\<0[oO]\=\o\+[Ll]\=\>"\n')
      f.write('"syn match   veraNumber  "\<0[xX]\\x\+[Ll]\=\>"\n')
      f.write('"syn match   veraNumber  "\<0[bB][01]\+[Ll]\=\>"\n')
      f.write('"syn match   veraNumber  "\<\%(\d*\|0\)[eE]\{0,1\}[Ll]\=\>"\n')
      f.write("\n")
      f.write('" List all of the VERA blocks\n')
      vblock = '/^\['+'\]\|\['.join(self.blocknames)+'\]/\n'
      f.write('syn match veraBlocks '+vblock)
      #vblock = ' '.join(self.blocknames)
      #f.write('syn keyword veraBlocklist '+vblock+'\n')
      #f.write('syn region veraBlocks start="[" end="]" contains=veraBlocklist\n')
      f.write("\n")
      f.write('" List all of the CASEID cards\n')
      for k, v in self.blocks.items():
        i = 0
        #clist = ' '.join(v.cardnames)
        #print('block =',v.name)
        #print(clist)
        clist = ''
        for card in v.cardnames:
          clist = clist + ' ' + card
          i+=1
          if i % 10 == 0:
            #print(clist)
            f.write('syn keyword vera'+v.name+'Cards '+clist+'\n')
            clist = ''
        #Add the remaining cards
        if i % 10 != 0:
          f.write('syn keyword vera'+v.name+'Cards '+clist+'\n')
      f.write("\n")
      f.write('syn keyword veraPreproc include\n')
      f.write("\n")
      f.write('let b:current_syntax = "vera"\n')
      f.write('hi def link veraSet       Special\n')
      f.write('hi def link veraSensOpts  Special\n')
      f.write('hi def link veraInt       Number\n')
      f.write('hi def link veraFloat     Number\n')
      f.write('hi def link veraNumber    Number\n')
      f.write('hi def link veraString    String\n')
      f.write('hi def link veraTodo      Todo\n')
      f.write('hi def link veraComment   Comment\n')
      f.write('hi def link veraPreproc   PreProc\n')
      f.write('hi def link veraBlocks    Statement\n')
      f.write('hi def link veraCards     Identifier\n')
      f.write('hi def link veraIsotope   Type\n')
      for k, v in self.blocks.items():
        f.write('hi def link vera'+v.name+'Cards   Identifier\n')


    #This is the creationg of the autocomplete/tab completion function for the VERA input.
    with open('autoload/verainputcomplete.vim','w') as f:
      f.write('"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++!\n')
      f.write('"                              Copyright (C) 2018                              !\n')
      f.write('"                   The Regents of the University of Michigan                  !\n')
      f.write('"              MPACT Development Group and Prof. Thomas J. Downar              !\n')
      f.write('"                             All rights reserved.                             !\n')
      f.write('"                                                                              !\n')
      f.write('" Copyright is reserved to the University of Michigan for purposes of          !\n')
      f.write('" controlled dissemination, commercialization through formal licensing, or     !\n')
      f.write('" other disposition. The University of Michigan nor any of their employees,    !\n')
      f.write('" makes any warranty, express or implied, or assumes any liability or          !\n')
      f.write('" responsibility for the accuracy, completeness, or usefulness of any          !\n')
      f.write('" information, apparatus, product, or process disclosed, or represents that    !\n')
      f.write('" its use would not infringe privately owned rights. Reference herein to any   !\n')
      f.write('" specific commercial products, process, or service by trade name, trademark,  !\n')
      f.write('" manufacturer, or otherwise, does not necessarily constitute or imply its     !\n')
      f.write('" endorsement, recommendation, or favoring by the University of Michigan.      !\n')
      f.write('"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++!\n')
      f.write('"\n')
      f.write('" Vim autocomplete function for VERA input files.\n')
      f.write('" Language: VERA Input file\n')
      f.write('" Maintainer: Dan Jabaay\n')
      f.write('" Latest Revision: 9/24/2019\n')
      f.write('"\n')
      f.write('fun! verainputcomplete#CompleteCards(findstart, base)\n')
      f.write('  if a:findstart\n')
      f.write('    " locate the start of the word\n')
      f.write('    let line = getline(\'.\')\n')
      f.write('    let stt = col(\'.\') - 1\n')
      f.write('    "This logic searches from the cursor and continues assuming the current\n')
      f.write('    "is a letter, number, or underscore.\n')
      f.write('    while stt > 0 && (line[stt - 1] != \' \') && (line[stt - 1] =~ \'\\a\' || line[stt - 1] == \'_\' || line[stt - 1] =~ \'\\d\' )\n')
      f.write('      let stt -= 1\n')
      f.write('    endwhile\n')
      f.write('    return stt\n')
      f.write('  else\n')
      f.write('    "Set the vim dictionaries, lists and variables here.\n')
      f.write('    let matches = []\n')
      f.write('    let defs = []\n')
      f.write('    "List of all the block names\n')
      f.write('    let blocks = verainputcomplete#getBlockNames()\n')
      f.write('    "Vim command to search up for the nearest block and get the name\n')
      f.write('    let blockname = verainputcomplete#getCurrentBlock()\n')
      f.write('    "Set the variable to access the list of cards in the block\n')
      f.write('    let blocknamecard = blockname . \'Cards\'\n')
      f.write('    let blockdict = verainputcomplete#getBlockDict()\n')
      f.write('    let definitiondict = verainputcomplete#getManualDict()\n')
      f.write('    "===========================================\n')
      f.write('    "Loop for finding the list of cards based on the blockname\n')
      f.write('    "that was found.  The manual dictionary entry is also added\n')
      f.write('    "if it is non-blank here.\n')
      f.write('    "\n')
      f.write('    "Check if the entry is blank\n')
      f.write('    let a:fullcard = ""\n')
      f.write('    let line = getline(\'.\')\n')
      f.write('    let stp = col(\'.\')-1\n')
      f.write('    let beforecursor = strpart(line,1,stp)\n')
      f.write('    let line_cardvaluepairs = split(beforecursor,\';\')\n')
      f.write('    "Get the most recent card_keyvalue from the current cursor location\n')
      f.write('    "trim any white space\n')
      f.write('    let lastpair = substitute(get(line_cardvaluepairs,-1),\' \',\'\',\'g\')\n')
      f.write('    let tmplist = split(get(line_cardvaluepairs,-1),\' \')\n')
      f.write('    "Eliminate the extra white space that gets added to the list by checking empty()\n')
      f.write('    let lastpairlist = []\n')
      f.write('    for l in tmplist\n')
      f.write('      if !empty(l)\n')
      f.write('        call add(lastpairlist,l)\n')
      f.write('      endif\n')
      f.write('    endfor\n')
      f.write('    let lastpaircardname = get(lastpairlist,0)\n')
      f.write('    let lastpairentry = get(lastpairlist,-1)\n')
      f.write('    let lastpairargnum = len(lastpairlist)\n')
      f.write('    let linepieces = split(beforecursor,\' \')\n')
      f.write('    let hdf5cards = [\'restart_read\', \'restart_write\', \'restart_shuffle\']\n')
      f.write('    "Loop for finding the list of cards based on the blockname\n')
      f.write('    "that was found.  The manual dictionary entry is also added\n')
      f.write('    "if it is non-blank here.\n')
      f.write('    for b in blocks\n')
      f.write('      if blockname ==# b\n')
      f.write('        "Check if the last card string\n')
      f.write('        let iscard = -1\n')
      f.write('        let iscard = index(blockdict[blocknamecard],lastpaircardname)\n')
      f.write('        "If we matched a fully named card from the list, return card dependent data\n')
      f.write('        if iscard >= 0\n')
      f.write('          "Check if the card needs an hdf5 file as the next argument\n')
      f.write('          let ishdf5 = -1\n')
      f.write('          let ishdf5 = index(hdf5cards,blockdict[blocknamecard][iscard])\n')
      f.write('          "Check if the last card was xsfilename\n')
      f.write('          if match(blockdict[blocknamecard][iscard],\'xs_filename\') == 0\n')
      f.write('            let defs = verainputcomplete#getXSFilenames()\n')
      f.write('          "include needs to be added as a card to all blocks.\n')
      f.write('          elseif match(blockdict[blocknamecard][iscard],\'include\') == 0\n')
      f.write('            let defs = verainputcomplete#getIncludeFilenames()\n')
      f.write('          elseif ishdf5 >= 0\n')
      f.write('            "return list of files\n')
      f.write('            if lastpairargnum == 1\n')
      f.write('              let defs = verainputcomplete#getRestartFilenames()\n')
      f.write('            "return list of labels from file\n')
      f.write('            elseif lastpairargnum == 2\n')
      f.write('              let defs = verainputcomplete#getRestartLabels(lastpairentry)\n')
      f.write('            endif " last pair arg\n')
      f.write('          "Add the default and optional values to the card if they exist.\n')
      f.write('          else\n')
      f.write('            let defs = verainputcomplete#getCardDefaultInputs(definitiondict[blockname . blockdict[blocknamecard][iscard] . \'dict\'])\n')
      f.write('          endif " is hdf5\n')
      f.write('        "Previous argument was not a card, generate list of cards for block based on started text\n')
      f.write('        else " is card\n')
      f.write('          for m in blockdict[blocknamecard]\n')
      f.write('            if m =~ \'^\' . a:base\n')
      f.write('              call add(defs,definitiondict[blockname . m . \'dict\'])\n')
      f.write('            endif\n')
      f.write('          endfor\n')
      f.write('        endif " is card\n')
      f.write('      endif " b is blockname\n')
      f.write('    endfor " b in blocks\n')
      f.write('    return {\'words\' : defs, \'refresh\' : \'always\'}\n')
      f.write('  endif " if a:findstart\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"Function to return list of block names\n')
      f.write('fun! verainputcomplete#getBlockNames()\n')
      f.write('  return [\''+'\', \''.join(self.blocknames)+'\']\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"Function to return the current block the cursor is in.\n')
      f.write('fun! verainputcomplete#getCurrentBlock()\n')
      f.write('  let l:first=getline(search(\'[\',\'bn\',\'1\'))[1:]\n')
      f.write('  return split(l:first,\']\')[0]\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"  This function parses the card manual dictionary entry and \n')
      f.write('"  returns the single string variable where every line from a \n')
      f.write('"  manual entry section is joined together.\n')
      f.write('fun! verainputcomplete#joinCardDictEntry(stt,stp,info)\n')
      f.write('  let l:dictentry = \'\'\n')
      f.write('  let l:bool = 0\n')
      f.write('  let l:indstt = match(a:info,a:stt)\n')
      f.write('  let l:indstp = match(a:info,a:stp)-1\n')
      f.write('  if l:indstp - l:indstt > 0\n')
      f.write('    let l:dictentry = join(a:info[l:indstt : l:indstp],(\' \'))\n')
      f.write('  else\n')
      f.write('    let l:dictentry = a:info[l:indstt]\n')
      f.write('  endif\n')
      f.write('  return l:dictentry\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"  This function parses the value default/applicable entry and \n')
      f.write('"  returns the word to add to the list and the optional description.\n')
      f.write('fun! verainputcomplete#parseCardDefault(entry)\n')
      f.write('  let l:desc = \'\'\n')
      f.write('  if (match(a:entry,\'(\') > 0) && (match(a:entry,\')\') > match(a:entry,\'(\'))\n')
      f.write('    let l:desc = a:entry[match(a:entry,\'(\'):match(a:entry,\')\')] . " "\n')
      f.write('    let l:word = substitute(a:entry[:match(a:entry,\'(\')-1]," ","","g")\n')
      f.write('  else\n')
      f.write('    let l:word = substitute(a:entry," ","","g")\n')
      f.write('  endif\n')
      f.write('  return [l:word, l:desc]\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"Function to return dictionary of default and eligible values for a given card\n')
      f.write('fun! verainputcomplete#getCardDefaultInputs(card)\n')
      f.write('  let l:blocks=[\'need\', \'units default\', \'units other\', \'value default\', \'values applicable\', \'limitations\', \'description\', \'notes\']\n')
      f.write('  let l:defs=[]\n')
      f.write('  let l:info=split(a:card[\'info\'],"\\n")\n')
      f.write('  for i in l:info\n')
      f.write('    if i =~# \'^value default\'\n')
      f.write('      "Trim "value default"\n')
      f.write('      let l:stt = \'^\' . l:blocks[3]\n')
      f.write('      let l:stp = \'^\' . l:blocks[4]\n')
      f.write('      let l:v = verainputcomplete#joinCardDictEntry(stt,stp,info)\n')
      f.write('      "Trim "value default"\n')
      f.write('      let l:v = substitute(l:v[15:-1],"[{}]","","g")\n')
      f.write('      "Check if there are multiple, comma separated applicable values\n')
      f.write('      if match(l:v,\',\') > 0\n')
      f.write('        let l:vals=split(l:v,\',\')\n')
      f.write('        for v in l:vals\n')
      f.write('          "Check if there are ()\'s, treat as additional menu description.\n')
      f.write('          let l:tmp = verainputcomplete#parseCardDefault(l:v)\n')
      f.write('          call add(l:defs,{\'word\' : l:tmp[0], \'menu\' : l:tmp[1] . "Default"})\n')
      f.write('        endfor\n')
      f.write('      "There\'s just one.\n')
      f.write('      else\n')
      f.write('        "Check if there are ()\'s, treat as additional menu description.\n')
      f.write('        let l:tmp = verainputcomplete#parseCardDefault(l:v)\n')
      f.write('        call add(l:defs,{\'word\' : l:tmp[0], \'menu\' : l:tmp[1] . "Default"})\n')
      f.write('      endif\n')
      f.write('    elseif i =~# \'^values applicable\'\n')
      f.write('      "Get every manual section line into a single string var.\n')
      f.write('      let l:stt = \'^\' . l:blocks[4]\n')
      f.write('      let l:stp = \'^\' . l:blocks[5]\n')
      f.write('      if match(l:info,l:stp) == -1\n')
      f.write('        let l:stp = \'^\' . l:blocks[6]\n')
      f.write('        if match(l:info,l:stp) == -1\n')
      f.write('          let l:stp = \'^\' . l:blocks[7]\n')
      f.write('        endif\n')
      f.write('      endif\n')
      f.write('      let l:v = verainputcomplete#joinCardDictEntry(stt,stp,info)\n')
      f.write('      "Trim "values applicable"\n')
      f.write('      let l:v = substitute(l:v[19:-1],"[\'{}]","","g")\n')
      f.write('      let l:v = substitute(l:v," or ","","g") \n')
      f.write('      let l:v = substitute(l:v," and ","","g")\n')
      f.write('      "Trim all options after the first period.  \n')
      f.write('      if match(l:v,\'\.\') > 0\n')
      f.write('        let l:v = l:v[:match(l:v,\'\.\')-1]\n')
      f.write('      endif\n')
      f.write('      "Check if there are multiple, comma separated applicable values\n')
      f.write('      if match(l:v,\',\') > 0\n')
      f.write('        let l:vals=split(l:v,\',\')\n')
      f.write('        for v in l:vals\n')
      f.write('          "Check if there are ()\'s, treat as additional menu description.\n')
      f.write('          let l:tmp = verainputcomplete#parseCardDefault(l:v) \n')
      f.write('          call add(l:defs,{\'word\' : l:tmp[0], \'menu\' : l:tmp[1]})\n')
      f.write('        endfor\n')
      f.write('      "There\'s just one.\n')
      f.write('      else\n')
      f.write('        "Check if there are ()\'s, treat as additional menu description.\n')
      f.write('        let l:tmp = verainputcomplete#parseCardDefault(l:v) \n')
      f.write('        call add(defs,{\'word\' : l:tmp[0], \'menu\' : l:tmp[1]})\n')
      f.write('      endif\n')
      f.write('    endif\n')
      f.write('  endfor\n')
      f.write('  return l:defs\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"Function to return dictionary of xs filenames\n')
      f.write('fun! verainputcomplete#getXSFilenames()\n')
      f.write('  let l:defs=[]\n')
      f.write('  let l:mpact_data = $MPACT_DATA\n')
      f.write('  "This is how you check if the ENV var exists.  Try to expand it.\n')
      f.write('  if l:mpact_data[0:1] != \'$\'\n')
      f.write('    "Get list of .fmt and .dat files\n')
      f.write('    let l:tmpxsfiles = systemlist(\'ls \' . l:mpact_data . \'/*.fmt \' . l:mpact_data . \'/*.dat\')\n')
      f.write('    "Loop over list\n')
      f.write('    for f in l:tmpxsfiles\n')
      f.write('      let l:tmplabel = \'\'\n')
      f.write('      "Set the library type based on the file extension\n')
      f.write('      if match(f[-4:],\'.fmt\') == 0\n')
      f.write('        let l:tmplabel = \'ORNL\'\n')
      f.write('      elseif match(f[-4:],\'.dat\') == 0\n')
      f.write('        let l:tmplabel = \'HELIOS\'\n')
      f.write('      endif\n')
      f.write('      call add(l:defs,{\'word\' : split(f,\'/\')[-1], \'menu\' : l:tmplabel, \'info\' : join([ ],(\'\'))})\n')
      f.write('    endfor\n')
      f.write('  endif\n')
      f.write('  return l:defs\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"Function to return dictionary of include filenames\n')
      f.write('fun! verainputcomplete#getIncludeFilenames()\n')
      f.write('  let l:defs=[]\n')
      f.write('  "Get list of .fmt and .dat files\n')
      f.write('  let l:tmpfiles = systemlist(\'ls ./*.ini\')\n')
      f.write('  "Loop over list\n')
      f.write('  for f in tmpfiles\n')
      f.write('    call add(l:defs,{\'word\' : split(f,\'/\')[-1], \'menu\' : \'\', \'info\' : join([ ],(\'\'))})\n')
      f.write('  endfor\n')
      f.write('  return l:defs\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"Function to return dictionary of hdf5 restart filenames\n')
      f.write('fun! verainputcomplete#getRestartFilenames()\n')
      f.write('  let l:defs=[]\n')
      f.write('  let l:tmphdf5files=systemlist(\'ls ./*.h5 ./*.res\')\n')
      f.write('  for f in l:tmphdf5files\n')
      f.write('    if match(f[-3:],\'.h5\') == 0 || match(f[-4:],\'.res\') == 0\n')
      f.write('      let l:firstlevels=systemlist(\'h5ls \' . f)\n')
      f.write('      let l:corename=l:firstlevels[0]\n')
      f.write('      let l:corename=substitute(l:corename[:-6],\' \',\'\',\'g\')\n')
      f.write('      let l:tmplabels=systemlist(\'h5ls \' . f . \'/\' . l:corename)\n')
      f.write('      let l:tmplabel=\'\'\n')
      f.write('      for l in l:tmplabels\n')
      f.write('        if match(l,\'RESTART\') == 0\n')
      f.write('          let l:tmplabel=l:tmplabel . substitute(l[8:-6],\' \',\'\',\'g\') . \',\'\n')
      f.write('        endif\n')
      f.write('      endfor\n')
      f.write('      call add(l:defs,{\'word\' : f, \'menu\' : l:tmplabel[:-2], \'info\' : join([ ],(\'\'))})\n')
      f.write('    endif\n')
      f.write('  endfor\n')
      f.write('  return l:defs\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('"Function to return dictionary of hdf5 restart filenames\n')
      f.write('fun! verainputcomplete#getRestartLabels(lastpairentry)\n')
      f.write('  let l:defs=[]\n')
      f.write('  "get the core name (CORE_Core)\n')
      f.write('  let l:firstlevels=systemlist(\'h5ls \' . a:lastpairentry)\n')
      f.write('  let l:corename=l:firstlevels[0]\n')
      f.write('  "Trim the trailing data\n')
      f.write('  let l:corename=substitute(l:corename[:-6],\' \',\'\',\'g\')\n')
      f.write('  "Get the next level of groups, which are the restart labels.\n')
      f.write('  let l:tmphdf5labels=systemlist(\'h5ls \' . a:lastpairentry . \'/\' . l:corename)\n')
      f.write('  for f in l:tmphdf5labels\n')
      f.write('    "If the group is a restart group.\n')
      f.write('    if match(f,\'RESTART\') == 0\n')
      f.write('      "Get the exposure for the corresponding label\n')
      f.write('      let l:tmppath = \' -d /\' . l:corename . \'/\' . substitute(f[:-6],\' \',\'\',\'g\') . \'/STATE/\'\n')
      f.write('      let l:exposures=systemlist(\'h5dump\' . l:tmppath . \'exposure\' . l:tmppath . \'exposure_efpd \' . a:lastpairentry )\n')
      f.write('      let l:bu = exposures[5]\n')
      f.write('      let l:efpd = exposures[12]\n')
      f.write('      "Remove the leading RESTART_ and ending Group from the h5ls output, and\n')
      f.write('      "leading space from the burnup values.\n')
      f.write('      call add(l:defs,{\'word\' : substitute(f[8:-6],\' \',\'\',\'g\'), \'menu\' : l:bu[7:] . \' GWD/MT,\' . l:efpd[7:] . \' EFPD\', \'info\' : join([ ],(\'\'))})\n')
      f.write('    endif\n')
      f.write('  endfor " hdf5 labels\n')
      f.write('  return l:defs\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('fun! verainputcomplete#getBlockDict()\n')
      f.write('  let l:dict={}\n')
      for k, v in self.blocks.items():
        v.cardnames.sort(key=str.lower)
        clist = '[\''+'\', \''.join(v.cardnames)+'\']\n'
        f.write('    let l:dict["'+v.name+'Cards"] = ' + clist)
      f.write('  return l:dict\n')
      f.write('endfun\n')
      f.write('"\n')
      f.write('fun! verainputcomplete#getManualDict()\n')
      f.write('    let l:dict = {}\n')
      for k, v in self.blocks.items():
        v.cardnames.sort(key=str.lower)
        #Add dictionary of cards here...
        for j, c in v.cards.items():
          f.write('    "The dictionary entries for card name '+c.name+'\n')
          f.write('    "List all the contents of the manual in the info entry.\n')
          f.write('    let l:dict["'+v.name+c.name+'dict"]={\n')
          f.write('        \ \'word\' : \''+c.name+'\',\n')
          f.write('        \ \'menu\' : \''+",".join([param['type'] for param in c.manual])+'\',\n')
          f.write('        \ \'info\' : join([\n')
          firstman=True
          for param in c.manual:
            if len(param['name']) > 0:
              if not firstman:
                f.write('        \ "'+r'\n'+'",\n')
              f.write('        \ "argument name = '+param['name']+r'\n'+'",\n')
              firstman=False
            if len(param['need']) > 0:
              f.write('        \ "need = '+param['need']+r'\n'+'",\n')
            if len(param['unitsdefault']) > 0:
              f.write('        \ "units default = '+param['unitsdefault']+r'\n'+'",\n')
            if len(param['unitsother']) > 0:
              f.write('        \ "units other = '+param['unitsother']+r'\n'+'",\n')
            if len(param['valuedefault']) > 0:
              f.write('        \ "value default = '+param['valuedefault']+r'\n'+'",\n')
            if len(param['valuesapplicable']) > 0:
              f.write('        \ "values applicable = '+param['valuesapplicable']+r'\n'+'",\n')
            if len(param['limitations']) > 0:
              f.write('        \ "limitations = '+param['limitations']+r'\n'+'",\n')
            if len(param['description']) > 0:
              f.write('        \ "description = '+param['description']+r'\n'+'",\n')
            if len(param['notes']) > 0:
              f.write('        \ "notes = '+param['notes']+r'\n'+'",\n')
          f.write('        \ ],(\'\'))}\n')
      f.write('  return l:dict\n')
      f.write('endfun\n')

#fun! CompleteMonths(findstart, base)
#  if a:findstart
#    " locate the start of the word
#    let line = getline('.')
#    let start = col('.') - 1
#    while start > 0 && line[start - 1] =~ '\a'
#      let start -= 1
#    endwhile
#    return start
#  else
#    " find months matching with "a:base"
#    let res = []
#    for m in split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec")
#      if m =~ '^' . a:base
#        call add(res, m)
#      endif
#    endfor
#    return res
#  endif
#endfun
#set completefunc=CompleteMonths


      #f.write('exec s:verablockssyntax')
      #let s:verablockssyntax = 'syn match veraBlocks ' . s:allblocks
      #exec s:verablockssyntax

  #def __getitem__(self,key):
  #  if self.isBlock(key):
  #    return self.blocks[key]
  #  else
  #    for blocks in self.blocknames:
  #      if self.isCardinBlock(blocks,key):
  #        return self.blocks[self.blocknames.find(name)].cards[key]

  #def getBlock(self,key):
  #  if self.isBlock(key):
  #    #if type(key) is int:
  #    #  return self.blocks[key]
  #    #else:
  #    #  return self.blocks[self.blocknames.index(key)]
  #    print(self.blocknames,self.blocknames.index(key))
  #    tmpblock = self.blocks[self.blocknames.index(key)]
  #  else:
  #    tmpblock = BLOCK('',[],[])

  #  return tmpblock
#File wide functions, makes the VERAIO cleaner to initialize
def findBounds(lines,sttstr,stpstr):
  lread = False
  readstart = 0
  readstop = len(lines)-1

  #Loop over lines in the directory file, look for blocks
  for i,line in enumerate(lines):
    #print(i,line.strip())
    if lread:
      #If we hit the end of the block list, exit the loop
      if line.rstrip() == stpstr:
        readstop = i
        break

    #Need to strip out the \n newline from the read of the file
    if line.rstrip() == sttstr:
      readstart = i+1
      lread = True

  return readstart, readstop

#Finds the list of names given a list of file lines and a line match string
def findNames(lines,namestr):
  tmpnames = []
  for i,line in enumerate(lines):
    #If we hit the end of the block list, exit the loop
    if namestr == '':
      tmpnames.append(line.strip())
    else:
      sttind = line.find(namestr)
      if sttind > 0:
        tmpnames.append(line.rstrip()[sttind+1:])

  #format the names, remove ':' at the end
  names = []
  for name in tmpnames:
    sttind = name.find(':')
    if sttind > 0:
      names.append(name[:sttind])
    else:
      names.append(name)

  return names

#Function to find the datatype indices
def findDTInd(lines,names,offset):
  ind = []
  for i,line in enumerate(lines):
    sttind = line.find('&')
    if sttind > 0:
      if line.rstrip()[sttind+1:] in names:
        ind.append(i+offset+1)
  ind.append(len(lines)+offset+1)

  return ind

def findVINBlockInd(lines,names,offset):
  ind = []
  newnames = []
  for i,line in enumerate(lines):
    if line.strip()[:-1] in names:
      ind.append(i+offset+1)
      newnames.append(line.strip()[:-1])
  ind.append(len(lines)+offset)

  return ind, newnames

################################################################################
# Main executable code.
curDir = os.path.dirname(os.path.realpath(__file__))
print('Generating vim dictionary for  "'+curDir+'/../scripts/Templates/Directory.yml"')
vin = VERAIO(curDir + '/../scripts/Templates/Directory.yml')

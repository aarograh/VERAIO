import VERADATATYPE as VDT
import VERACARD as VC

class BLOCK:
  'A class to generalize a VERAIn input BLOCK'

  #The block init routine.  Takes a block name and a list of lines for the block.
  def __init__(self,name,lines,dts):
    self.isinit = False
    self.name = name
    self.ncards = 0
    self.cardnames = []
    self.cards = {}

    dtnames = list(dts.keys())
    tmpdt = VDT.DATATYPE('',[])
    self.datatype = tmpdt

    #Loop over the lines, look for card indices
    cind = {}
    cnames = []
    hasdef = False
    hasdefs = {}
    definds = {}
    tables = {}
    for i, line in enumerate(lines):
      sline = line.split()
      if sline:
        if ("VERAInputTable" in line):
          for someline in lines[i:]:
            if someline[:2] == "  " and someline.rstrip()[-1] == ":":
              card_name = someline.strip()[:-1]
              break
          table_lines = []
          for someline in lines[i:]:
            someSline = someline.split()
            if len(someSline) > 1:
              if someSline[0] == "#>" and someSline[1] == "}":
                if card_name in tables:
                  tables[card_name].append(table_lines)
                else:
                  tables[card_name] = [table_lines]
                break
              else:
                table_lines.append(someline)
          hasdef = True
          hasdefs[card_name] = True
        if (line[0] != '#') and (line[2] != ' ') and (line[2] != '<') and (line[2] != '_'):
          card_name = line.strip()[:-1]
          self.cardnames.append(card_name)
          if not hasdef:
            hasdefs[card_name] = False
            definds[card_name] = 0
          else:
            definds[card_name] = i
          table_lines = []
          for someline in lines[i:]:
            if someline.startswith("#>"):
              if card_name in tables:
                tables[card_name].append(table_lines)
              else:
                tables[card_name] = [table_lines]
              break
            else:
              table_lines.append(someline)
          hasdef = False
        elif (len(line) > 2) and (line[2] == '<'):
          if line.rstrip()[line.find("*")+1:] in dtnames:
            self.datatype = dts[line.rstrip()[line.find("*")+1:]]

    i = 0
    for icard, card in enumerate(self.cardnames):
      self.cards[card] = VC.CARD(card,hasdefs[card],tables[card],dts)
      i += len(tables[card])

    self.ncards = i

    if self.name != '' and self.ncards > 0 and len(self.cards) > 0:
      self.isinit = True


  #Edit routine for the block, and all added cards
  def edit(self,indent=0):
    print(' ' * indent + '  BLOCK ========')
    print(' ' * indent + '    name   =',self.name)
    print(' ' * indent + '    ncards =',self.ncards)
    self.datatype.edit(indent+2)
    for k, v in self.cards.items():
      v.edit(indent+2)

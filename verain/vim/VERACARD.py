import VERADATATYPE as VDT

class CARD:
  'A class to generalize a VERAIn input card within a block'

  #The card init routine.  Takes a card name and a list of lines for the card.
  def __init__(self,name,hasdef,lines,dts):
    self.name = name
    self.manual = []
    self.checks = []
    self.style = ''

    dtnames = list(dts.keys())
    tmpdt = VDT.DATATYPE('',[])
    self.datatype = tmpdt
    #for dt in dts:
      #dtnames.append(dt.name)

    readchecks = False
    if hasdef:
      for table in lines[:-1]:
        self.manual.append(self.initman())
        self.readman(table)
    for i,line in enumerate(lines[-1]):
      #Check if the line is a datatype
      if line.rstrip()[line.find("*")+1:] in dtnames:
        self.datatype = dts[line.rstrip()[line.find("*")+1:]]
      elif "_style:" in line:
        self.style = line.rstrip()[line.find(":")+1:]
      elif "_check:" in line:
        readchecks = True
      elif readchecks:
        tmpline = line.rstrip()[line.find("-")+2:]
        if (tmpline != '') and (tmpline.find(":") == -1):
          self.checks.append(line.rstrip()[line.find("-")+2:])


    #print('CARDNAME = ',self.name)
    #self.type = type
    #Loop over all of the checks,


  #  self.value = value

  #def checkValues(self):
    #Loop over all of the values in the list, perform the checks on the values.

  #Edit routine for the card
  def edit(self,indent=0):
    print(' ' * indent +'  CARD       =')
    print(' ' * indent +'    name     =',self.name)
    print(' ' * indent +'    manual   =',self.manual)
    print(' ' * indent +'    style    =',self.style)
    print(' ' * indent +'    checks   =',self.checks)
    self.datatype.edit(indent+2)

  #Read the manual entry
  def initman(self):
    man = {}
    # Initialize entries to blank
    man['name']=''
    man['type']=''
    man['need']=''
    man['unitsdefault']=''
    man['unitsother']=''
    man['valuedefault']=''
    man['valuesapplicable']=''
    man['limitations']=''
    man['description']=''
    man['notes']=''

    return man

  #Read the manual entry
  def readman(self,lines):
    for i,line in enumerate(lines):
      #print(i,line.rstrip())
      if "VERAInputTable" in line or line.strip() == '':
        continue
      eqind=line.find('=')
      if(eqind > 0):
        entry=line.strip()[2:eqind]
        entry=entry.strip()
        #print(eqind,entry)
        if(line.strip()[-1] == '%') or (line.strip()[-2:] == '},'):
          tmp=line.strip()[line.find('{')+1:-2]
          tmp=tmp.replace('"','\\\'')
          self.manual[-1][entry]=tmp.strip()
        elif(line.strip()[-1] == '}'):
          tmp=line.strip()[line.find('{')+1:-1]
          tmp=tmp.replace('"','\\\'')
          self.manual[-1][entry]=tmp.strip()
        else:
          tmp=line.strip()[line.find('{')+1:]
          tmp=tmp.replace('"','\\\'')
          self.manual[-1][entry]=tmp.strip()
      else:
        tmp=line.strip()[2:]
        tmp=tmp.replace('"','\\\'')
        if(line.strip()[-1] == '%') or (line.strip()[-2:] == '},'):
          #print(line.rstrip()[-1],'% or ',line.rstrip()[-2:],'},')
          tmp=tmp.strip()[:-2]
          self.manual[-1][entry]=self.manual[-1][entry] +' '+r'\n'+'",\n\\ "' + tmp.strip()
        elif(line.strip()[-1] == '}'):
          tmp=tmp.strip()[:-1]
          self.manual[-1][entry]=self.manual[-1][entry] +' '+r'\n'+'",\n\\ "' + tmp.strip()
        else:
          self.manual[-1][entry]=self.manual[-1][entry] +' '+r'\n'+'",\n\\ "' + tmp.strip()
      #Latex things we want to strip out completely
      self.manual[-1][entry]=self.manual[-1][entry].replace('$','')
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'\begin{itemize','')
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'\end{itemize','')
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'\begin{enumerate','')
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'\end{enumerate','')
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'\texttt','')

      #Latex things we want to replace with something else
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'\newline',r'\n')
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'\times ','*')
      self.manual[-1][entry]=self.manual[-1][entry].replace(r'*10^','E')
      self.manual[-1][entry]=self.manual[-1][entry].replace('\item','*')
      self.manual[-1][entry]=self.manual[-1][entry].replace('\_','_')
      self.manual[-1][entry]=self.manual[-1][entry].replace('\'s ','s ')
      self.manual[-1][entry]=self.manual[-1][entry].replace('`','\'')
      self.manual[-1][entry]=self.manual[-1][entry].replace('n\'t ',' not ')

    #print(man["description"])

    #return man


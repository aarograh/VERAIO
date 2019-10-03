class DATATYPE:
  'A class to set some attributes on the datatype object'

  def __init__(self,name,lines):
    self.initnull()
    self.name = name

    #print(name)
    tmplist = []
    for i,line in enumerate(lines):
      tmplist = line.split()
      if tmplist[0] == '_parse:':
        self.parse = tmplist[1].replace("'",'')
      elif tmplist[0] == '_type:':
        self.type = tmplist[1].replace("'",'')
      elif tmplist[0] == '_named:':
        self.named = tmplist[1].find('1') >= 0

    if self.type == '':
      self.type = self.parse

    if self.name != '' and self.parse != '' and self.type != '':
      self.isinit = True

    #self.edit()

  def initnull(self):
    self.isinit = False
    self.name = ''
    self.named = False
    self.parse = ''
    self.type = ''

  def edit(self,indent=0):
    print(' ' * indent + '  DATATYPE   =')
    print(' ' * indent + '    name     =',self.name)
    print(' ' * indent + '    isinit   =',self.isinit)
    print(' ' * indent + '    named    =',self.named)
    print(' ' * indent + '    parse    =',self.parse)
    print(' ' * indent + '    type     =',self.type )
    #self.isBlock =

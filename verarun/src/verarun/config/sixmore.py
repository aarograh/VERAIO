import io

try:
  FILE_TYPES = ( file, io.IOBase )
except NameError:
  FILE_TYPES = ( io.IOBase, )


def is_file( fparam ):
  return  isinstance( fparam, FILE_TYPES )

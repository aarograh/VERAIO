#!/usr/bin/env python
#------------------------------------------------------------------------
#       NAME:           pbs.py                                          -
#       HISTORY:                                                        -
#               2020-03-20      leerw@ornl.gov                          -
#         Added create_{account,project}_directive() methods and PBSPro
#         class.
#               2020-03-05      leerw@ornl.gov                          -
#         Added work_dir_env property.
#               2020-03-03      leerw@ornl.gov                          -
#               2020-03-02      leerw@ornl.gov                          -
#------------------------------------------------------------------------
from __future__ import print_function
import argparse, logging, os, re
import subprocess, sys, time, traceback
from datetime import datetime

import pdb


REGEX_JOB_ID = re.compile( r'^(\d+).*$' )
REGEX_WS = re.compile( r'[,\s]+' )


#------------------------------------------------------------------------
#       FUNCTION:       create_instance()                               -
#------------------------------------------------------------------------
def create_instance( name, log_func ):
  """
  Args:
      name (str): case-sensitive class name
"""
  #pbs_class = name.capitalize()
  pbs = eval( name + '( log_func )' )

  return  pbs
#end create_instance


#------------------------------------------------------------------------
#       FUNCTION:       get_pbs()                                       -
#------------------------------------------------------------------------
def get_pbs( log_func ):
  """
"""
  pbs = pbs_class = None

#               -- Check environment first
  if os.environ.get( 'VERA_SBATCH' ):
    pbs_class = Slurm
  elif os.environ.get( 'VERA_QSUB' ):
    pbs_class = Torque

#               -- Check path
  if pbs_class is None:
    args = [ '/bin/bash', '-c', 'type -p sbatch' ]
    for cls, command in ( ( Slurm, 'sbatch' ), ( Torque, 'qsub' ) ):
      args[ 2 ] = 'type -p ' + command
      try:
        results = subprocess.check_output( args )
        pbs_class = cls
        break
      except:
        pass

#               -- Instantiate
  if pbs_class is not None:
    try:
      pbs = pbs_class( log_func )
    except:
      pass

  return  pbs
#end get_pbs


#------------------------------------------------------------------------
#       CLASS:          PBS                                             -
#------------------------------------------------------------------------
class PBS( object ):
  """
PBS operations
  command to execute:   qsub                    sbatch
  env:                  VERA_QSUB               ???
  dependency:           -W depend=afterok:{0}   --dependency=afterok:{0}
  command output:       NNNN.host.name          Submitted batch job NNNN
                        extract_job_id()

submit_job()
script_extension
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         PBS.__init__()                                  -
  #----------------------------------------------------------------------
  def __init__( self,
      script_extension,
      job_id_env,
      job_name_env,
      work_dir_env,
      log_func = None
      ):
    """
"""
    self._job_id_env = job_id_env
    self._job_name_env = job_name_env
    self._log_func = log_func
    self._script_extension = script_extension
    self._work_dir_env = work_dir_env
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         PBS.check_job_status()                          -
  #----------------------------------------------------------------------
  def check_job_status( self, job_id ):
    """Check the status of the specified job.
Noop to be overridden by subclasses.
    Args:
        job_id (str): job id
    Returns:
        str: status text
"""
    return  ''
  #end check_job_status


  #----------------------------------------------------------------------
  #     METHOD:         PBS.create_account_directive()                  -
  #----------------------------------------------------------------------
  def create_account_directive( self, account_name ):
    """Create job script directive to specify an account.
Noop to be overridden by subclasses.
    Args:
        account_name (str): name of account to add
    Returns:
        str: directive string, empty if account_name is empty
"""
    return  ''
  #end create_account_directive


  #----------------------------------------------------------------------
  #     METHOD:         PBS.create_project_directive()                  -
  #----------------------------------------------------------------------
  def create_project_directive( self, project_name ):
    """Create job script directive to specify a project.
Noop to be overridden by subclasses.
    Args:
        project_name (str): name of project to add
    Returns:
        str: directive string, empty if project_name is empty
"""
    return  ''
  #end create_project_directive


  #----------------------------------------------------------------------
  #     METHOD:         PBS.log()                                       -
  #----------------------------------------------------------------------
  def log( self, *args, **kwargs ):
    """
"""
    if self._log_func:
      self._log_func( *args, **kwargs )
  #end log


  #----------------------------------------------------------------------
  #     METHOD:         PBS.submit_job()                                -
  #----------------------------------------------------------------------
  def submit_job( self, script_name, wait_job_id ):
    """Execute command to submit the specified script.
Noop to be overridden by subclasses.  Whereas the job_id is the integer
string representing the job ID, the job_name is the full
text output by the PBS after the job submission.
    Args:
        script_name (str): name of PBS script file, assumed to be in the
            current directory
        wait_job_id (str): optional job id on which this case depends
    Returns:
        tuple: ( job_id(str), job_name(str) )
"""
    return  '', ''
  #end submit_job


#               -- Properties
#               --

  job_id_env = property( lambda self: self._job_id_env )
  """Name of job ID env variable"""

  job_name_env = property( lambda self: self._job_name_env )
  """Name of job name env variable"""

  script_extension = property( lambda self: self._script_extension )
  """Extension for PBS script files sans '.'"""

  work_dir_env = property( lambda self: self._work_dir_env )
  """Name of work directory env variable"""

#end PBS


#------------------------------------------------------------------------
#       CLASS:          Slurm                                           -
#------------------------------------------------------------------------
class Slurm( PBS ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         Slurm.__init__()                                -
  #----------------------------------------------------------------------
  def __init__( self, log_func = None ):
    """
"""
#   if sys.version_info.major == 3:
#     super().__init__( logger )
#   else:
#     super( Slurm, self ).__init__( logger )
    PBS.__init__(
        self, 'sbatch',
        'SLURM_JOB_ID', 'SLURM_JOB_NAME', 'SLURM_SUBMIT_DIR',
        log_func
        )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         Slurm.check_job_status()                        -
  #----------------------------------------------------------------------
  def check_job_status( self, job_id ):
    """Check the status of the specified job.
    Args:
        job_id (str): job id
    Returns:
        str: status text
"""
    args = [ 'squeue', '--job', str( job_id ) ]
    results = subprocess.check_output( args )
    results = results.decode( 'utf-8' )
    return  results
  #end check_job_status


  #----------------------------------------------------------------------
  #     METHOD:         Slurm.create_account_directive()                -
  #----------------------------------------------------------------------
  def create_account_directive( self, account_name ):
    """Create job script directive to specify an account.
    Args:
        account_name (str): name of account to add
    Returns:
        str: directive string, empty if account_name is empty
"""
    return  '#SBATCH --account=' + account_name  if account_name else  ''
  #end create_account_directive


  #----------------------------------------------------------------------
  #     METHOD:         Slurm.create_project_directive()                -
  #----------------------------------------------------------------------
  def create_project_directive( self, project_name ):
    """Create job script directive to specify a project.
    Args:
        project_name (str): name of project to add
    Returns:
        str: directive string, empty if project_name is empty
"""
    return  '#SBATCH --account=' + project_name  if project_name else  ''
  #end create_project_directive


  #----------------------------------------------------------------------
  #     METHOD:         Slurm.submit_job()                              -
  #----------------------------------------------------------------------
  def submit_job( self, script_name, wait_job_id ):
    """Execute command to submit the specified script.
    Args:
        script_name (str): name of PBS script file, assumed to be in the
            current directory
        wait_job_id (str): optional job id on which this case depends
    Returns:
        tuple: ( job_id(str), job_name(str) )
"""
    vera_sbatch = os.environ.get( 'VERA_SBATCH' )
    if vera_sbatch:
      args = REGEX_WS.split( vera_sbatch.lstrip( '\t ' ) )
    else:
      args = [ 'sbatch' ]

    if wait_job_id:
      args.append( '-d' )
      args.append( 'afterok:{0}'.format( wait_job_id ) )
    args.append( script_name )
    self.log( 'submitting job: ' + str( args ) )
    job_name = subprocess.check_output( args )
    job_name = job_name.decode( 'utf-8' )
    job_name = job_name.rstrip( '\r\n' )
    self.log( 'job name: ' + job_name )

    job_tokens = REGEX_WS.split( job_name )
    job_id = job_tokens[ -1 ] if job_tokens  else -1
    #job_id = int( job_tokens[ -1 ] ) if job_tokens  else -1

    return  job_id, job_name
  #end submit_job

#end Slurm


#------------------------------------------------------------------------
#       CLASS:          Torque                                          -
#------------------------------------------------------------------------
class Torque( PBS ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         Torque.__init__()                               -
  #----------------------------------------------------------------------
  def __init__( self, log_func = None ):
    """
"""
#   if sys.version_info.major == 3:
#     super().__init__( logger )
#   else:
#     super( Torque, self ).__init__( logger )
    PBS.__init__(
        self, 'pbs',
        'PBS_JOBID', 'PBS_JOBNAME', 'PBS_O_WORKDIR',
        log_func
        )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         Torque.check_job_status()                       -
  #----------------------------------------------------------------------
  def check_job_status( self, job_id ):
    """Check the status of the specified job.
    Args:
        job_id (str): job id
    Returns:
        str: status text
"""
    args = [ 'qstat', str( job_id ) ]
    results = subprocess.check_output( args )
    results = results.decode( 'utf-8' )
    return  results
  #end check_job_status


  #----------------------------------------------------------------------
  #     METHOD:         Torque.create_account_directive()               -
  #----------------------------------------------------------------------
  def create_account_directive( self, account_name ):
    """Create job script directive to specify an account.
    Args:
        account_name (str): name of account to add
    Returns:
        str: directive string, empty if account_name is empty
"""
    return  '#PBS -A ' + account_name  if account_name else  ''
  #end create_account_directive


  #----------------------------------------------------------------------
  #     METHOD:         Torque.create_project_directive()               -
  #----------------------------------------------------------------------
  def create_project_directive( self, project_name ):
    """Create job script directive to specify a project.
    Args:
        project_name (str): name of project to add
    Returns:
        str: directive string, empty if project_name is empty
"""
    return  '#PBS -A ' + project_name  if project_name else  ''
  #end create_project_directive


  #----------------------------------------------------------------------
  #     METHOD:         Torque.submit_job()                             -
  #----------------------------------------------------------------------
  def submit_job( self, script_name, wait_job_id ):
    """Execute command to submit the specified script.
    Args:
        script_name (str): name of PBS script file, assumed to be in the
            current directory
        wait_job_id (str): optional job id on which this case depends
    Returns:
        tuple: ( job_id(str), job_name(str) )
"""
    vera_qsub = os.environ.get( 'VERA_QSUB' )
    if vera_qsub:
      args = REGEX_WS.split( vera_qsub.lstrip( '\t ' ) )
    else:
      args = [ 'qsub' ]

    if wait_job_id:
      args.append( '-W' )
      args.append( 'depend=afterok:{0}'.format( wait_job_id ) )
    args.append( script_name )
    self.log( 'submitting job: ' + str( args ) )
    job_name = subprocess.check_output( args )
    job_name = job_name.decode( 'utf-8' )
    job_name = job_name.rstrip( '\r\n' )
    self.log( 'job name: ' + job_name )
    m = REGEX_JOB_ID.match( job_name )
    job_id = m.group( 1 ) if m  else None
    #job_id = int( m.group( 1 ) ) if m  else -1

    return  job_id, job_name
  #end submit_job

#end Torque


#------------------------------------------------------------------------
#       CLASS:          PBSPro                                          -
#------------------------------------------------------------------------
class PBSPro( Torque ):
  """
"""


#               -- Object Methods
#               --


  #----------------------------------------------------------------------
  #     METHOD:         PBSPro.__init__()                               -
  #----------------------------------------------------------------------
  def __init__( self, log_func = None ):
    """
"""
#   if sys.version_info.major == 3:
#     super().__init__( logger )
#   else:
#     super( PBSPro, self ).__init__( logger )
    Torque.__init__( self, log_func )
  #end __init__


  #----------------------------------------------------------------------
  #     METHOD:         PBSPro.create_project_directive()               -
  #----------------------------------------------------------------------
  def create_project_directive( self, project_name ):
    """Create job script directive to specify a project.
    Args:
        project_name (str): name of project to add
    Returns:
        str: directive string, empty if project_name is empty
"""
    return  '#PBS -P ' + project_name  if project_name else  ''
  #end create_project_directive

#end PBSPro


#------------------------------------------------------------------------
#       NAME:           main()                                          -
#------------------------------------------------------------------------
if __name__ == '__main__':
  PBS.main()

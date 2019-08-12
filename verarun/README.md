# verarun

A package and script for creating and submitting VERA jobs on a cluster.


# Packages and Modules

| Package        | Module    | Classes                      |
| -------------- | --------- | ---------------------------- |
| verarun        | runner    | VeraRunner                   |
|                | verain    | VeraInputXMLDoc              |
| verarun.config | config    |                              |
|                | hostinfo  | HostInfo, Specs              |
|                | sixmore   |                              |
| verarun.job    | verajob   | VeraJobParams, VeraJobScript |


# Execution

When the *verarun* package is installed, a script name `verarun` is also
installed.  Execute `verarun` from the command line without parameters to
get a usage dump.

    $ verarun
    usage: vrun.py [-h] [--dry-run] [-e EMAIL_ADDRS [EMAIL_ADDRS ...]]
               [-c HOST_CONFIG_FILE] [--hostname HOSTNAME] [-i INPUT_PATH]
               [-l] [-m PROC_MEM] [-n NPROCS] [-d VERA_DIR]
               [--vera-installs-dir VERA_INSTALLS_DIR] [-v VERA_VERSION]
               [-t WALLTIME]
    ...

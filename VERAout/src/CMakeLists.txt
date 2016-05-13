#creating the hdf5tosilocc executable - what a wacky name...
TRIBITS_ADD_EXECUTABLE(
    hdf5tosilocc
    SOURCES hdf5tosilo.cc
    NOEXEPREFIX
    NOEXESUFFIX
    INSTALLABLE
)

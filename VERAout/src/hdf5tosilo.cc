//----------------------------------*-C++-*----------------------------------//
/*!
 * \file   src/hdf5tosilo.cc
 * \author Andrew Godfrey and Cole Gentry
 * \date   04/23/2014
 * \
 * \brief  Tool meant to convert files from HDF5 format to SILO format
 * \note   Copyright (C) 2012 Oak Ridge National Laboratory, UT-Battelle, LLC.
 */
//---------------------------------------------------------------------------//

#include <iostream>
#include <iomanip>
#include <string>
#include <sstream>
#include <list>
#include <fstream>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <silo.h>
#include "hdf5.h"

 using namespace std;

 list<string> datasets;
 list<string> statepoints;
 int depth;
 int numstate;
 bool recurse;
 bool dsonly;

herr_t op_func(hid_t loc_id, const char *name, const H5L_info_t *info, void *operator_data); 

int main( int argc, char *argv[] )
{
//HDF5 related variables
 hid_t      dset, space;
 herr_t     status;
 int        h_ndims, maxndim;

//subroutine
 void groupIterate(hid_t loc_id);
 string class_name(hid_t);
 string  type_name(hid_t);

/*****************************************************************************
READ IN ARGUMENT FOR INPUT FILE TO BE CONVERTED
*****************************************************************************/
 if (argc!=2)
 {
   cout << "\nusage:  hdf5tosilo.exe  input_hdf5_file\n\n";
   return 1;
 }

 string inputfilename = argv[1];

 cout << "|-----------------------------------|\n";
 cout << "|   VERA HDF5 -> SILO Converter     |\n";
 cout << "|                                   |\n";
 cout << "|  Cole Gentry and Andrew Godfrey   |\n";
 cout << "|      Rev. 2.0   7/3/2014          |\n";
 cout << "|-----------------------------------|\n";
 cout << "Input File: " << inputfilename << "\n";

 hid_t h_file=H5Fopen(inputfilename.c_str(), H5F_ACC_RDONLY, H5P_DEFAULT);

 if (h_file<0)
 {
   cout <<"\nerror: input file " << inputfilename << " does not exist\n\n";
   return 1;
 }

// get base name for output silo files (1 per statepoint)
 unsigned ndx = inputfilename.rfind(".");
 string basefile;
 if (ndx==0)
 {
   basefile = inputfilename;
 }
 else
 {
   basefile = inputfilename.substr(0,ndx);
 }

// try to get the veraout_version number
 int version = -1;
 string dataset = "veraout_version";
 bool exists = H5Lexists(h_file, dataset.c_str(), H5P_DEFAULT);
 if (exists)
 {
   dset = H5Dopen(h_file,dataset.c_str(), H5P_DEFAULT);
   if (dset<0)
   {
      cout <<"\nerror: could not open dataset " << dataset << "\n\n";
      return 1;
   }
   cout << "Reading dataset " << dataset << "\n";
   H5Dread(dset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT,&version);
   H5Dclose(dset);
 }

// determine the default group for the pin powers data (to get geometry)
// if prior to veraout assume the root folder
// then check it exists 
 string defgroup = "";
 if (version>=0)
 {
   defgroup = "/STATE_0001";
   exists = H5Lexists(h_file, defgroup.c_str(), H5P_DEFAULT);
   if (!exists)
   {
     cout <<"\nerror: could not open group " << defgroup << " for version " << version << "\n";
     return 1;
   }
 }

// determine the default group for the core data 
// if version 2 use CORE group else use the root
 string coregroup = "";
 if (version == 1)
 {
   coregroup="/CORE";     
   exists = H5Lexists(h_file, coregroup.c_str(), H5P_DEFAULT);
   if (!exists)
   {
      cout <<"\nerror: could not open group " << coregroup << " for version " << version << "\n";
      return 1;
   }
  }

// Find either pin_powers or pin_powers_1

 dataset = defgroup+"/pin_powers";
 exists = H5Lexists(h_file, dataset.c_str(), H5P_DEFAULT);
 if (exists) 
 { 
   dset = H5Dopen (h_file,dataset.c_str(), H5P_DEFAULT);
   if (dset<0)
   {
      cout <<"\nerror: could not open dataset " << dataset << "\n\n";
      return 1;
   }
 }
 else
 {
   dataset = defgroup+"/pin_powers_1";
   exists = H5Lexists(h_file, dataset.c_str(), H5P_DEFAULT);
   if (exists) 
   { 
     dset = H5Dopen(h_file,dataset.c_str(), H5P_DEFAULT);
     if (dset<0)
     {
        cout <<"\nerror: could not open dataset " << dataset << "\n\n";
        return 1;
     }
   }
 }
 if (!exists)
 {
    cout << "\n error: HDF file must contain pin_powers or pin_powers_1 datasets\n";
    return 1;
 }

/*****************************************************************************
READ IN ALL NECESSARY DIMENSIONS AND DATA FROM HDF5 FILE FROM DEFAULT DATASET
*****************************************************************************/

 space = H5Dget_space (dset);
 maxndim = H5Sget_simple_extent_ndims(space);
 hsize_t h_dims[maxndim];
 h_ndims = H5Sget_simple_extent_dims(space, h_dims, NULL);
 if (h_ndims!=4) 
 {
   cout << "\nerror: pin power data has wrong dimensions\n";
   return 1;
 }
 
 int nass  = h_dims[3];
 int nax   = h_dims[2];
 int npini = h_dims[1];
 int npinj = h_dims[0];
 int nchni = npini+1;
 int nchnj = npinj+1;

 status=H5Sclose(space);
 status=H5Dclose(dset);

// get core map dimensions if is more than 1 assembly

 int nassi=1;
 int nassj=1;

 exists = false;
 if (nass > 1)
 {
   dataset = coregroup+"/core_map";
   exists = H5Lexists(h_file, dataset.c_str(), H5P_DEFAULT);
   if (exists)
   {
     dset = H5Dopen(h_file,dataset.c_str(), H5P_DEFAULT);
     if (dset<0)
     {
       cout <<"\nerror: could not open dataset " << dataset << "\n\n";
       return 1;
     }


     hid_t cm_space = H5Dget_space(dset);
     int cm_maxndim = H5Sget_simple_extent_ndims(cm_space);
     hsize_t cm_dims[cm_maxndim];
     int cm_ndims = H5Sget_simple_extent_dims(cm_space, cm_dims, NULL);
     if (cm_ndims != 2) 
     {
       cout << "\nerror: core map data has wrong dimensions\n";
       return 1;
     }

     nassi = cm_dims[1];
     nassj = cm_dims[0];

     H5Sclose(cm_space);
   }
   else
   {
     cout << "\nerror:  core map not found\n\n";
     return 1;
   }
 }

 int coremap[nassi][nassj];

 if (exists)
 {
     cout << "Reading dataset " << dataset << "\n";
     int *cm_tmp = new int[nassi*nassj];
     H5Dread(dset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, cm_tmp);
     H5Dclose(dset);

     for (int i = 0; i < nassi; i++)  
       for (int j = 0; j < nassj; j++)  
         coremap[i][j] = cm_tmp[i+j*nassi];
 }
 else
 {
   coremap[0][0]=1;
 }

// get the core symmetry

 int sym = 1;
 dataset = coregroup+"/core_sym";
 exists = H5Lexists(h_file, dataset.c_str(), H5P_DEFAULT);
 if (exists)
 {
   dset = H5Dopen(h_file,dataset.c_str(), H5P_DEFAULT);
   if (dset<0)
   {
      cout <<"\nerror: could not open dataset " << dataset << "\n\n";
      return 1;
   }
   cout << "Reading dataset " << dataset << "\n";
   H5Dread(dset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT,&sym);
   H5Dclose(dset);
 }
 else
 {
   cout << "\nwarnng: full symmetry is assumed\n\n";
 }
 if (sym != 1 && sym != 4) 
 {
   cout << "\nerror:  cannot support symmetry flag of " << sym << "\n\n";
   return 1;
 }

// try to get the assembly pitch

 double apitch;
 dataset = coregroup+"/apitch";
 exists = H5Lexists(h_file, dataset.c_str(), H5P_DEFAULT);
 if (exists)
 {
   dset = H5Dopen(h_file,dataset.c_str(), H5P_DEFAULT);
   if (dset<0)
   {
      cout <<"\nerror: could not open dataset " << dataset << "\n\n";
      return 1;
   }
   cout << "Reading dataset " << dataset << "\n";
   status=H5Dread(dset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT,&apitch);
   status=H5Dclose(dset);
 }
 else
 {
   apitch=21.5;
   cout << "Default assembly pitch being used: " << apitch << " cm\n";
 }

// print final geometry summary 

 cout << "\n VERAOut Version = " << version << "\n";
 cout << "\nData Dimensions:\n";
 cout << "  Number of Fuel Rods Across : " << npini << "\n";
 cout << "  Number of Fuel Rods Down   : " << npinj << "\n";
 cout << "  Number of Axial Levels     : " << nax   << "\n";
 cout << "  Number of Total Assemblies : " << nass  << "\n";
 cout << "  Core symmetry flag         : " << sym   << "\n";
 if (nass > 1)
 {
   cout << "  Number of Assemblies Across: " << nassi << "\n";
   cout << "  Number of Assemblies Down  : " << nassj << "\n";
   cout << "  Core map is:\n";
   for (int j=0; j<nassj; j++)
   {
     cout << "   ";
     for (int i=0;i<nassi; i++)
     {
       cout << setfill(' ') << setw(3) << coremap[i][j];
     }
     cout << endl;
   }
   cout << endl;
 }
 


// get axial edit bounds
 
 dataset = coregroup+"/axial_mesh";
 exists = H5Lexists(h_file, dataset.c_str(), H5P_DEFAULT);
 if (exists)
 {
   dset = H5Dopen(h_file,dataset.c_str(), H5P_DEFAULT);
   if (dset<0)
   {
      cout <<"\nerror: could not open dataset " << dataset << "\n\n";
      return 1;
   }
 }
 else if (nax>1)
 {
    cout << "\n error: HDF file does not contain an axial_mesh dataset\n";
    return 1;
 }

 double *axmesh = new double[nax+1];
 if (dset<0 && nax==1)
 {
   cout << "Assuming Axial Height of 1.0 cm\n";
   axmesh[0]=0.0;
   axmesh[1]=1.0;
 }
 else
 {
   cout << "Reading dataset " << dataset << "\n";
   H5Dread(dset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT,axmesh);
   H5Dclose(dset);
 }

//set sizes and starting index based on symmetry

 int mpini = nassi*npini;  // number of fuel pins across the core
 int mpinj = nassj*npinj;  // number of fuel pins down the core
 int massi = nassi;        // nnumber of fuel assemblies accross the core
 int massj = nassj;        // number of fuel assemblies down  the core
 int mchni = nassi*nchni;  // number of coolant channels accross the the core
 int mchnj = nassj*nchnj;  // number of coolant channel down the core
 int mnodi = nassi*2;      // number of nodes
 int mnodj = nassj*2;      // number of nodes
 
 int ipx = 0;  // starting indices for pins
 int ipy = 0;
 int iax = 0;  // starting indices for assemblies
 int iay = 0;
 int icx = 0;  // starting indices for channels
 int icy = 0;
 int inx = 0;  // starting indices for nodes
 int iny = 0;

 if (sym == 4)
 {
   if (mpini % 2 > 0)
     mpini = truncl(mpini/2.0)+1;      // odd
   else
     mpini = nearbyintl(mpini/2.0);    //even
     
   if (mpinj % 2 > 0)
     mpinj = truncl(mpinj/2.0)+1;      // odd
   else
     mpinj = nearbyintl(mpinj/2.0);    //even

   if (massi % 2 > 0)
     massi = truncl(massi/2.0)+1;      // odd
   else
     massi = nearbyintl(massi/2.0);    //even

   if (massj % 2 > 0)
     massj = truncl(massj/2.0)+1;      // odd
   else
     massj = nearbyintl(massj/2.0);    //even

   if (mchni % 2 > 0)
     mchni = truncl(mchni/2.0)+1;      // odd
   else
     mchni = nearbyintl(mchni/2.0);    //even

   if (mchnj % 2 > 0)
     mchnj = truncl(mchnj/2.0)+1;      // odd
   else
     mchnj = nearbyintl(mchnj/2.0);    //even

   mnodi = nearbyintl(mnodi/2.0); 
   mnodj = nearbyintl(mnodj/2.0); 

   if (npini % 2 == 0)
   {
     ipx = nearbyintl(npini/2.0);  // initial starting pin index for cut geometry
     ipy = nearbyintl(npinj/2.0);  // remember indices are zero based
     iax = (int)nassj/2.0;  
     iay = (int)nassj/2.0;
     icx = (int)nchnj/2.0;
     icy = (int)nchnj/2.0;
     inx = 1;
     iny = 1;
   }
   else
   {
     ipx = (int)npini/2.0;  // initial starting pin index for cut geometry
     ipy = (int)npinj/2.0;  // remember indices are zero based
     iax = (int)nassj/2.0;  
     iay = (int)nassj/2.0;
     icx = nearbyintl(nchnj/2.0);
     icy = nearbyintl(nchnj/2.0);
     inx = 1;
     iny = 1;
   }
 }

/*calculate radial and axial meshes for each type of output
-- 0 = 3D pin mesh
-- 1 = 2D pin mesh
-- 2 = 3D assembly mesh (1x1 per assembly)
-- 3 = 2D assembly mesh (1x1 per assembly)
-- 4 = 3D channel mesh
-- 5 = 2D channel mesh
-- 6 = 3D nodal mesh
-- 7 = 2D nodal mesh
-- 8 = 1D axial mesh
--
-- Gap is ignored.  
-- Effective Pin pitch is Assembly Pitch devided by number of rods
*/

 bool is3D = nax > 1;
 bool isQtr = sym == 4;
 bool isEvenPin = npini % 2 == 0;
 bool isEvenAss = nassi % 2 == 0;
 bool cutpin = isQtr && !isEvenPin;
 bool cutass = isQtr && !isEvenAss;

 int ndims[9] = {3,2,3,2,3,2,3,2,1};

 int dims[9][3]={ {mpini+1,mpinj+1,nax+1},
                  {mpini+1,mpinj+1      },
                  {massi+1,massj+1,nax+1},
                  {massi+1,massj+1      },
                  {mchni+1,mchnj+1,nax+1},
                  {mchni+1,mchnj+1      },
                  {mnodi+1,mnodj+1,nax+1},
                  {mnodi+1,mnodj+1      },
                  {nax+1                } };

 double *px = new double[mpini+1];
 double *py = new double[mpinj+1];
 double *ax = new double[massi+1];
 double *ay = new double[massj+1];
 double *cx = new double[mchni+1];
 double *cy = new double[mchnj+1];
 double *nx = new double[mnodi+1];
 double *ny = new double[mnodj+1];
 double *z  = new double[nax+1];

 double *coords[9][3]={ {px,py,z},
                        {px,py},
                        {ax,ay,z},
                        {ax,ay},
                        {cx,cy,z},
                        {cx,cy},
                        {nx,ny,z},
                        {nx,ny},
                        {z} };

 double dpx = apitch / npini;
 double dpy = apitch / npinj;
 double dcx = apitch / nchni; 
 double dcy = apitch / nchnj;

 px[0]=0.0;
 px[1]=cutpin ? dpx/2.0 : dpx;
 for(int i=2;i<=mpini;i++)
 {
   px[i]=px[i-1]+dpx;
 }

// py[0]=0.0;
// py[1]=cutpin ? dpy/2.0 : dpy;
// for(int j=2;j<=mpinj;j++)
// {
//   py[j]=py[j-1]+dpy;
// }

 py[0]=0.0;
 for(int j=1;j<mpinj;j++)
 {
   py[j]=py[j-1]+dpy;
 }
 py[mpinj]=cutpin ? dpy/2.0 : dpy;
 py[mpinj]+=py[mpinj-1];

 ax[0]=0.0;
 ax[1]=cutass ? apitch/2.0 : apitch;
 for(int i=2;i<=massi;i++)
 {
   ax[i]=ax[i-1]+apitch;
 }

 ay[0]=0.0;
 for(int j=1;j<massj;j++)
 {
   ay[j]=ay[j-1]+apitch;
 }
 ay[massj]=cutass ? apitch/2.0 : apitch;
 ay[massj]+=ay[massj-1];

 cx[0]=0.0;
 cx[1]=!cutpin ? dcx/2.0 : dcx;
 for(int i=2;i<=mchni;i++)
 {
   cx[i]=cx[i-1]+dcx;
 }

 cy[0]=0.0;
 cy[1]=!cutpin ? dcy/2.0 : dcy;
 for(int j=2;j<=mchnj;j++)
 {
   cy[j]=cy[j-1]+dcy;
 }

 nx[0]=0.0;
 for(int i=1;i<=mnodi;i++)
 {
   nx[i]=nx[i-1]+apitch/2.0;
 }

 ny[0]=0.0;
 for(int j=1;j<=mnodj;j++)
 {
   ny[j]=ny[j-1]+apitch/2.0;
 }

 z[0]=axmesh[0];
 for(int k=1;k<=nax;k++)
 {
   z[k]=axmesh[k];
 }

 cout << "\n 3D Pin Mesh Boundaries\n";
 cout << "------------------------\n";
 for(int i=0;i<dims[0][0];i++)
 {
   cout << "i=" << i + ipx << " x=" << coords[0][0][i] << "\n";
 }
 cout << endl;
 for(int j=0;j<dims[0][1];j++)
 {
   cout << "j=" << j + ipy << " y=" << coords[0][1][j] << "\n";
 }
 cout << endl;
 for(int k=0;k<dims[0][2];k++)
 {
   cout << "k=" << k << " z=" << coords[0][2][k] << "\n";
 }

 cout << "\n 2D Assembly Mesh Boundaries\n";
 cout << "-----------------------------\n";
 for(int i=0;i<dims[3][0];i++)
 {
   cout << "i=" << i + iax << " x=" << coords[3][0][i] << "\n";
 }
 cout << endl;
 for(int j=0;j<dims[3][1];j++)
 {
   cout << "j=" << j + iay << " y=" << coords[3][1][j] << "\n";
 }

/* cout << "\n 2D Channel Mesh Boundaries\n";
 cout << "-----------------------------\n";
 for(int i=0;i<dims[5][0];i++)
 {
   cout << "i=" << i + icx << " x=" << coords[5][0][i] << "\n";
 }
 cout << endl;
 for(int j=0;j<dims[5][1];j++)
 {
   cout << "j=" << j + icy << " y=" << coords[5][1][j] << "\n";
 }

 cout << "\n 2D Nodal Mesh Boundaries\n";
 cout << "-----------------------------\n";
 for(int i=0;i<dims[7][0];i++)
 {
   cout << "i=" << i + inx << " x=" << coords[7][0][i] << "\n";
 }
 cout << endl;
 for(int j=0;j<dims[7][1];j++)
 {
   cout << "j=" << j + iny << " y=" << coords[7][1][j] << "\n";
 }*/

// iterate through groups and datasets, print out the tree, and store the
// statepoint groups so we can loop through them

 cout << "\n HDF5 objects\n";
 cout << "----------------\n";
 depth = 0;
 numstate = 0;
 recurse = true;
 dsonly = false;
 groupIterate(h_file); 
 recurse = false;
 dsonly = true;

// Print the info about the statepoints found

 cout << "\n=======================================================\n";
 cout << "  Statepoints Existing on the File\n";
 cout << "=======================================================\n";
 cout << "  Number of statepoints = " << numstate << "\n";
 for (list<string>::iterator it = statepoints.begin(); it != statepoints.end(); it++)
 {
   cout << "      " << *it << "\n";
 }

// open group for CORE if exists
 hid_t h_core = 0;
 exists = H5Lexists(h_file,"CORE", H5P_DEFAULT);
 if (exists)
   h_core = H5Oopen(h_file,"CORE",H5P_DEFAULT);
 
// start loop over statepoints 
 for(int nstate=0;nstate<=numstate;nstate++)
 {
   string outfile;
   hid_t h_state;
   if (nstate==0)
   {
     cout << "\n=======================================================\n";
     cout << " Converting Data for Root Level\n";

// for root level, clear the dataset list and get new one
     if (numstate==0)
     {
       outfile = basefile + ".silo";
     }
     else
     {
       outfile = basefile + "_root.silo";
     }
     h_state = h_file;
   }
   else
   {
     stringstream ss;
     ss << "/STATE_" << setfill('0') << setw(4) << nstate;

     cout << "\n=======================================================\n";
     cout << " Converting Data for Statepoint " << ss.str() << "\n";

// open statepoint group
     h_state = H5Oopen(h_file, ss.str().c_str(),H5P_DEFAULT);

     stringstream bs;
     if (numstate>1)
     {
       bs << basefile << "_" << setfill('0') << setw(4) << nstate<< ".silo";
     }
     else
     {
       bs << basefile << ".silo";
     }
     outfile = bs.str();
   }

// get the statepoint exposure, if it exists
   double exposure = 0.0;
   dataset="exposure";
   exists = H5Lexists(h_state, dataset.c_str(), H5P_DEFAULT);
   if (!exists)  // backwards compatibility
   {
     dataset="exposure_GWDMT";
     exists = H5Lexists(h_state, dataset.c_str(), H5P_DEFAULT);
   }
   if (exists)
   {
     dset = H5Dopen(h_state, dataset.c_str(), H5P_DEFAULT);
     if (dset<0) 
     {
       cout <<"\nerror: could not open dataset " << dataset << "\n\n";
       return 1;
     }
     cout << "Reading dataset " << dataset;
     H5Dread(dset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, &exposure);
     H5Dclose(dset);
     cout << " Exposure " << exposure << " GWd/MT\n";
   }

// make option list for each file
   DBoptlist *optlist = DBMakeOptlist(1);
   DBAddOption(optlist, DBOPT_DTIME, &exposure);

// for each statepoint, clear the dataset list and get new one
   depth = 0;
   datasets.clear();
   groupIterate(h_state); 
   int scnt = datasets.size();
   if (exists)   //add datasets for CORE group into every file
   {
     if (numstate>0 && nstate>0)
     {
       cout << " = CORE datasets = \n";
       groupIterate(h_core); 
     }
   }

// create a new SILO file for this statepoint
   DBfile *newdbfile=DBCreate(outfile.c_str(), DB_CLOBBER, DB_LOCAL, NULL, DB_HDF5);

//loop through each dataset.  Get the dimensions and type.  If the dimensions
//match one of the nine scenarios, flag it and write it to the SILO file

   bool    used_mesh[9] = {false,false,false,false,false,false,false,false,false};
   string mesh_label[9] = {"3D_Pin_Mesh", 
                           "2D_Pin_Mesh", 
                           "3D_Assembly_Mesh", 
                           "2D_Assembly_Mesh", 
                           "3D_Channel_Mesh", 
                           "2D_Channel_Mesh", 
                           "3D_Nodal_Mesh", 
                           "2D_Nodal_Mesh", 
                           "1D_Axial_Mesh"};

   int dscnt = datasets.size();
   cout << dscnt << " datasets found:\n";
   int added = 0;
   int ndx = 0;

   for (list<string>::iterator it = datasets.begin(); it != datasets.end(); it++)
   {
     ndx++;
     dataset = *it;
     int meshndx = -1;
     if (ndx>scnt)
       dset = H5Dopen(h_core , dataset.c_str(), H5P_DEFAULT);
     else
       dset = H5Dopen(h_state, dataset.c_str(), H5P_DEFAULT);

     //first, check type.  Has to be integer or double
     hid_t tid = H5Dget_type(dset);
     hid_t native = H5Tget_native_type(tid, H5T_DIR_ASCEND);
     hid_t classs = H5Tget_class(tid);
   
     if (ndx==1) cout << endl;
     cout << " - " << dataset.c_str();
     cout << " {" << class_name(classs) << "}";
   //cout << "   type is " << type_name(native) << "\n";

     H5Tclose(tid);
     if (classs != H5T_FLOAT)
     {
       cout << endl;
       H5Tclose(native);
       H5Dclose(classs);
       H5Dclose(dset);
       continue;
     }
     H5Dclose(classs);

     //next check dimensions
     hid_t sid = H5Dget_space(dset);
     maxndim = H5Sget_simple_extent_ndims(sid);
     hsize_t h_dims[maxndim];
     h_ndims = H5Sget_simple_extent_dims(sid, h_dims, NULL);
     H5Sclose(sid);

     if (h_ndims>0) 
     {
       cout << " " << h_ndims << ":(";
       for(int i=0;i<h_ndims;i++)
       {
         cout << h_dims[i];
         if (i<h_ndims-1)
           cout << " ";
         else
           cout << ")";
       }
     }
     cout << endl;
   
     if (h_ndims == 4) 
     {
       if (h_dims[3] == nass  &&
           h_dims[2] == nax   &&
           h_dims[1] == npini && 
           h_dims[0] == npinj) 
       {
         meshndx = is3D ? 0 : 1;
       }
       else if (h_dims[3] == nass  &&
                h_dims[2] == nax   &&
                h_dims[1] == nchni && 
                h_dims[0] == nchnj) 
       {
         meshndx = is3D ? 4 : 5;
       }
     }
     else if (h_ndims == 3)
     {
       if (h_dims[2] == nass  &&
           h_dims[1] == npini && 
           h_dims[0] == npinj) 
       {
         meshndx = 1;
       }
       else if (h_dims[2] == nass  &&
                h_dims[1] == nchni && 
                h_dims[0] == nchnj) 
       {
         meshndx = 5;
       }
       else if (h_dims[2] == nass  &&
                h_dims[1] == nax   && 
                h_dims[0] == 4    ) 
       {
         meshndx = is3D ? 6 : 7;
       }
     }
     else if (h_ndims == 2)
     {
       if (h_dims[1] == nass  &&
           h_dims[0] == nax)     
       {
         meshndx = is3D ? 2 : 3;
       }
       else if (h_dims[1] == nass  &&
                h_dims[0] == 4)     
       {
         meshndx = 7;
       }
     }
     else if (h_ndims == 1 && h_dims[0]>1)
     {
       if (h_dims[0] == nass) 
       {
         meshndx = 3;
       }
       else if (h_dims[0] == nax) 
       {
         meshndx = 8;
       }
     }

     if (meshndx < 0)
     {
       H5Tclose(native);
       H5Dclose(dset);
       continue;
     }
  
   //cout << "   < mesh index is " << meshndx << ": " << mesh_label[meshndx] << "\n";
  
// ok, we got here so lets finally allocate the data array and get the dataset values

     int size = 1;
     for(int i=0;i<h_ndims;i++)
       size *= h_dims[i];
  
     cout << "\nReading dataset " << dataset.c_str() << "\n";

     double *hdata = new double[size];
     status=H5Dread(dset, native, H5S_ALL, H5S_ALL, H5P_DEFAULT, hdata);

     H5Tclose(native);
     H5Dclose(dset);

// create dimensions and data for writing to SILO file

     int sdims[ndims[meshndx]];
     size=1;
     for (int i=0;i<ndims[meshndx];i++)
     {
       sdims[i]=dims[meshndx][i]-1;
       size *= sdims[i];
     }

     double *sdata = new double[size];

     if (meshndx==0) 
     {
       int count=0;
       for (int k=0; k<nax; k++)
       {
         for(int aj=nassj-1; aj>=iay; aj--)
       //for(int aj=iay; aj<nassj; aj++)
         {
           int iy = (aj == iay) ? ipy : 0;
           for(int pj=npinj-1; pj>=iy; pj--)
         //for(int pj=iy; pj<npinj; pj++)
           {
             for(int ai=iax; ai<nassi; ai++)
             {
               int a = coremap[ai][aj]-1;
               int ix = (ai == iax) ? ipx : 0;
               for(int pi=ix; pi<npini; pi++)
               {
                 if (a<0 || a>=nass)
                 {
                   sdata[count]=0.0;
                 }
                 else
                 {
                   //int ndx = pj+pi*npinj+k*npini*npinj+a*npini*npinj*nax;
                   int ndx = a+k*nass+pi*nass*nax+pj*nass*nax*npini;
                   sdata[count]=hdata[ndx];
                 }
                 count++;
               }
             }
           }
         }
       }
     }
     else if (meshndx==1)
     {
       int count=0;
       for(int aj=nassj-1; aj>=iay; aj--)
     //for(int aj=iay; aj<nassj; aj++)
       {
         int iy = (aj == iay) ? ipy : 0;
         for(int pj=npinj-1; pj>=iy; pj--)
       //for(int pj=iy; pj<npinj; pj++)
         {
           for(int ai=iax; ai<nassi; ai++)
           {
             int a = coremap[ai][aj]-1;
             int ix = (ai == iax) ? ipx : 0;
             for(int pi=ix; pi<npini; pi++)
             {
               if (a<0 || a>=nass)
               {
                 sdata[count]=0.0;
               }
               else
               {
                 //int ndx = pj+pi*npinj+a*npini*npinj;
                 int ndx = a+pi*nass+pj*nass*npini;
                 sdata[count]=hdata[ndx];
               }
               count++;
             }
           }
         }
       }
     }
     else if (meshndx==2)
     {
       int count=0;
       for (int k=0; k<nax; k++)
       {
         for(int aj=nassj-1; aj>=iay; aj--)
       //for(int aj=iay; aj<nassj; aj++)
         {
           for(int ai=iax; ai<nassi; ai++)
           {
             int a = coremap[ai][aj]-1;
             if (a<0 || a>=nass)
             {
               sdata[count]=0.0;
             }
             else
             {
               sdata[count]=hdata[a+k*nass];
             }
             count++;
           }
         }
       }
     }
     else if (meshndx==3)
     {
       int count=0;
       for(int aj=nassj-1; aj>=iay; aj--)
     //for(int aj=iay; aj<nassj; aj++)
       {
         for(int ai=iax; ai<nassi; ai++)
         {
           int a = coremap[ai][aj]-1;
           if (a<0 || a>=nass)
           {
             sdata[count]=0.0;
           }
           else
           {
             sdata[count]=hdata[a];
           }
           count++;
         }
       }
     }
     else if (meshndx==4)
     {
       int count=0;
       for (int k=0; k<nax; k++)
       {
         for(int aj=nassj-1; aj>=iay; aj--)
       //for(int aj=iay; aj<nassj; aj++)
         {
           int iy = (aj == iay) ? icy : 0;
           for(int cj=nchnj-1; cj>=iy; cj--)
         //for(int cj=iy; cj<nchnj; cj++)
           {
             for(int ai=iax; ai<nassi; ai++)
             {
               int a = coremap[ai][aj]-1;
               int ix = (ai == iax) ? icx : 0;
               for(int ci=ix; ci<nchni; ci++)
               {
                 if (a<0 || a>=nass)
                 {
                   sdata[count]=0.0;
                 }
                 else
                 {
                   //int ndx = cj+ci*nchnj+k*nchni*nchnj+a*nchni*nchnj*nax;
                   int ndx = a+k*nass+ci*nass*nax+cj*nass*nax*nchni;
                   sdata[count]=hdata[ndx];
                 }
                 count++;
               }
             }
           }
         }
       }
     }
     else if (meshndx==5)
     {
       int count=0;
       for(int aj=nassj-1; aj>=iay; aj--)
     //for(int aj=iay; aj<nassj; aj++)
       {
         int iy = (aj == iay) ? icy : 0;
         for(int cj=nchnj-1; cj>=iy; cj--)
       //for(int cj=iy; cj<nchnj; cj++)
         {
           for(int ai=iax; ai<nassi; ai++)
           {
             int a = coremap[ai][aj]-1;
             int ix = (ai == iax) ? icx : 0;
             for(int ci=ix; ci<nchni; ci++)
             {
               if (a<0 || a>=nass)
               {
                 sdata[count]=0.0;
               }
               else
               {
                 //int ndx = cj+ci*nchnj+a*nchni*nchnj;
                 int ndx = a+ci*nass+cj*nass*nchni;
                 sdata[count]=hdata[ndx];
               }
               count++;
             }
           }
         }
       }
     }
     else if (meshndx==6)
     {
       int count=0;
       for (int k=0; k<nax; k++)
       {
         for(int aj=nassj-1; aj>=iay; aj--)
       //for(int aj=iay; aj<nassj; aj++)
         {
           int iy = (aj == iay) ? iny : 0;
           for(int nj=1; nj>=iy; nj--)
         //for(int nj=iy; nj<2; nj++)
           {
             for(int ai=iax; ai<nassi; ai++)
             {
               int a = coremap[ai][aj]-1;
               int ix = (ai == iax) ? inx : 0;
               for (int ni=ix; ni<2; ni++)
               {
                 if (a<0 || a>=nass)
                 {
                   sdata[count]=0.0;
                 }
                 else
                 {
                   //int ndx = ni+nj*2+k*4+a*4*nax;
                   int ndx = a+k*nass+ni*nass*nax+nj*nass*nax*2;
                   sdata[count]=hdata[ndx];
                 }
                 count++;
               }
             }
           }
         }
       }
     }
     else if (meshndx==7)
     {
       int count=0;
       for(int aj=nassj-1; aj>=iay; aj--)
     //for(int aj=iay; aj<nassj; aj++)
       {
         int iy = (aj == iay) ? iny : 0;
         for(int nj=1; nj>=iy; nj--)
       //for(int nj=iy; nj<2; nj++)
         {
           for(int ai=iax; ai<nassi; ai++)
           {
             int a = coremap[ai][aj]-1;
             int ix = (ai == iax) ? inx : 0;
             for (int ni=ix; ni<2; ni++)
             {
               if (a<0 || a>=nass)
               {
                 sdata[count]=0.0;
               }
               else
               {
                 //int ndx = ni+nj*2+a*4;
                 int ndx = a+ni*nass+nj*nass*2;
                 sdata[count]=hdata[ndx];
               }
               count++;
             }
           }
         }
       }
     }
     else if (meshndx==8)
     {
       for(int k=0;k<nax;k++)
       {
         sdata[k]=hdata[k];
       }
     }
  
// write mesh and datasets to file

     if (meshndx<8)
     {
       if (!used_mesh[meshndx])
       {
         used_mesh[meshndx] = true;
         cout << "Writing mesh " << mesh_label[meshndx] << ": size is " << ndims[meshndx] << " - ";
         for (int i=0; i<ndims[meshndx]; i++)
           cout << dims[meshndx][i] << " ";
         cout << endl;
  
         DBPutQuadmesh(newdbfile,mesh_label[meshndx].c_str(), NULL,coords[meshndx],dims[meshndx],ndims[meshndx],
                                                                         DB_DOUBLE,DB_COLLINEAR,optlist);  
       }
  
       cout << "Writing dataset " << dataset.c_str() << " to SILO file for " << mesh_label[meshndx] << " with dims ";
       for (int i=0; i<ndims[meshndx]; i++)
         cout << sdims[i] << " ";
       cout << endl << endl;


       DBPutQuadvar1(newdbfile, dataset.c_str(), mesh_label[meshndx].c_str(), sdata, sdims, ndims[meshndx], 
                                                                     NULL, 0, DB_DOUBLE, DB_ZONECENT, optlist);
       added++;

// for 3D assembly mesh, write 1D Curve data for each assembly

       if (meshndx==2 && nass>1)
       {
         double xs[nax];
         for (int k=0;k<nax;k++)
           xs[k]=0.5*(z[k+1]+z[k]);
  
         for (int a=0;a<nass;a++)
         {
           double ys[nax];
           for (int k=0;k<nax;k++)
             ys[k]=hdata[a+k*nass];
  
             std::stringstream ss;
             ss<<dataset<<"_"<<(a+1);
             cout << "Writing dataset " << ss.str() << " to SILO file for " << mesh_label[6] << 
                                                                " with length " << nax << "\n";

             DBPutCurve(newdbfile, (ss.str()).c_str(), ys, xs, DB_DOUBLE, nax, optlist);
             added++;
         }
         cout << "\n";
       }
     }
     else
     {
       double xs[nax];
       for (int k=0;k<nax;k++)
         xs[k]=0.5*(z[k+1]+z[k]);

       cout << "Writing dataset " << dataset.c_str() << " to SILO file for " << mesh_label[meshndx] << 
                                                                  " with length " << sdims[0] << "\n\n";
       DBPutCurve(newdbfile, dataset.c_str(), sdata, xs, DB_DOUBLE, sdims[0], optlist);
       added++;
     }

// for 3D pin_powers, create a special assembly power dataset
//
     if (meshndx<=1 && nass > 1) 
     {
       if (dataset=="pin_powers") 
       {  
		 int sdims[ndims[2]];
         size=1;
         for (int i=0;i<ndims[2];i++)
         {
           sdims[i]=dims[2][i]-1;
           size *= sdims[i];
         }
		 
         size=massi*massj*nax;
         double *sdata = new double[size];

         int count=0;
         for (int k=0; k<nax; k++)
         {
           for(int aj=nassj-1; aj>=iay; aj--)
           {
             for(int ai=iax; ai<nassi; ai++)
             {
               int a = coremap[ai][aj]-1;
               if (a<0 || a>=nass)
               {
                 sdata[count]=0.0;
               }
               else
               {
                 int pcnt=0;
                 int iy = (aj == iay) ? ipy : 0;
                 for(int pj=npinj-1; pj>=iy; pj--)
                 {
                   int ix = (ai == iax) ? ipx : 0;
                   for(int pi=ix; pi<npini; pi++)
                   {
                     int ndx = a+k*nass+pi*nass*nax+pj*nass*nax*npini;
                     sdata[count]+=hdata[ndx];
                     if (hdata[ndx]>0)
                     {
                       pcnt=pcnt+1;
                     }
                   }
                 }
                 sdata[count]=sdata[count]/pcnt;
               }
               count++;
             }
           }
         }

         if (!used_mesh[2])
         {
           used_mesh[2] = true;
           cout << "Writing mesh " << mesh_label[2] << ": size is " << ndims[2] << " - ";
           for (int i=0; i<ndims[2]; i++)
             cout << dims[2][i] << " ";
           cout << endl;
  
           DBPutQuadmesh(newdbfile,mesh_label[2].c_str(), NULL,coords[2],dims[2],ndims[2],
                                                                           DB_DOUBLE,DB_COLLINEAR,optlist);  
         }
  
       cout << "Writing dataset " << "assy_powers" << " to SILO file for " << mesh_label[2] << " with dims ";
       for (int i=0; i<ndims[2]; i++)
         cout << sdims[i] << " ";
       cout << endl << endl;


       DBPutQuadvar1(newdbfile, "assy_powers", mesh_label[2].c_str(), sdata, sdims, ndims[2], 
                                                                     NULL, 0, DB_DOUBLE, DB_ZONECENT, optlist);

       }
     }
   }

// close statepoint SILO file and option list

   DBFreeOptlist(optlist);
   DBClose(newdbfile);
   if (added>0)
   {
     cout << added << " datasets added!\n";
     cout << "Wrote SILO file " << outfile << "\n";
   }
   else
   {
     cout << "No data written! Deleting SILO data.\n";
     int mm = remove(outfile.c_str());
     //cout << outfile << " deleted. Code =" << mm << "\n";
   }
   H5Gclose(h_state);
 }

// close input HDF5 file

if (exists)
  H5Gclose(h_core);
   
 H5Fclose(h_file);
 cout << "Done!\n";
 return 0;
}


//Iterate through Group
void groupIterate(hid_t loc_id)
{
  depth += 1;
  H5Literate(loc_id, H5_INDEX_NAME, H5_ITER_NATIVE, NULL, op_func, NULL);
  depth -= 1;
}

/*
 * Operator function. - Loops Recursively
 */
herr_t op_func(hid_t loc_id, const char *name, const H5L_info_t *info, void *opdata)
{
    stringstream ss; 
    ss  << " ";
    for(int i=0;i<depth;i++)
    {
      ss << "-";
    }
    ss << " " << name;

    hid_t id = H5Oopen(loc_id, name, H5P_DEFAULT);

    /*
     * Get type of the object and display its name and type.
     * The name of the object is passed to this function by 
     * the Library. Some magic :-)
     */
    H5O_info_t obj;
    H5Oget_info(id, &obj);
    switch (obj.type) {
    case H5G_GROUP: 
         //printf(" Object with name %s is a group \n", name);

         if (!dsonly)
         {
           bool skip=false;
           if (recurse)
           {
             if (string(name)=="INPUT" || 
                 string(name)=="INPUT_PARAMETER_LIST")
             {
               ss << " << skipped! >>";
               skip=true;
             }
           }

           cout << ss.str() << "\n";
           //store the STATEPOINT group names
           if (depth==1)
           {  
             if (string(name).substr(0,6)=="STATE_")
             {
               statepoints.push_back(name);
               numstate+=1;
             }
           }

           if (recurse && !skip)
             groupIterate(id);
         }
         break;
    case H5G_DATASET: 
         //printf(" Object with name %s is a dataset \n", name);
         cout << ss.str() << "\n";
         if (depth==1) 
         {
           datasets.push_back(name);
         }
         break;
    case H5G_TYPE: 
         //printf(" Object with name %s is a named datatype \n", name);
         break;
    default:
         //printf(" Unable to identify an object ");
         //return 0;
         break;
    }
    return 0;
 }

string class_name(hid_t cls)
{
  switch (cls){
  case H5T_INTEGER:
    return "Integer";
  case H5T_FLOAT:
    return "Float";
  case H5T_STRING: 
    return "string";
  case H5T_BITFIELD: 
    return "BitField";
  case H5T_OPAQUE: 
    return "Opaque";
  case H5T_COMPOUND: 
    return "Compound";
  case H5T_REFERENCE: 
    return "Reference";
  case H5T_ENUM: 
    return "Enum";
  case H5T_VLEN: 
    return "VLen";
  case H5T_ARRAY:
    return "Array";
  default:
    return "Unknown";
  }
} 

string type_name(hid_t typ)
{
  if (typ==H5T_NATIVE_DOUBLE)
    return "Double";
  else
    return "Unknown";
}

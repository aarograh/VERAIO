#include <sys/stat.h>
#include <iomanip>

#include "VERAIn_XML_Utils.hpp"

#include "Teuchos_CommandLineProcessor.hpp"
#include "Teuchos_ParameterList.hpp"
#include "Teuchos_XMLParameterListHelpers.hpp"
#include "Teuchos_DefaultComm.hpp"


using namespace std;
using namespace Teuchos;


VERAIn_XML::VERAIn_XML( const string & xml_file )
{
  comm_ = rcp( new SerialComm<int> );
  param_list_ = rcp( new ParameterList );
  updateParametersFromXmlFileAndBroadcast( xml_file, Teuchos::Ptr<Teuchos::ParameterList>(&*param_list_), *comm_);
}

// -------------------------------------------------------------

VERAIn_XML::~VERAIn_XML()
{
}

// -------------------------------------------------------------

string VERAIn_XML::downstring(const string & s)
{
  string t = s;
  for(unsigned int i = 0; i < t.length(); i++)
    t[i] = tolower(t[i]);
  return(t);
}

// -------------------------------------------------------------

string VERAIn_XML::trim_string(const string& input)
{
  string::size_type beginpos = input.find_first_not_of(" \t");
  string::size_type endpos = input.find_last_not_of(" \t");

  if (beginpos == string::npos || endpos == string::npos)
    return "";

  ++endpos;
  return input.substr(beginpos, endpos-beginpos);
}

// -------------------------------------------------------------

vector<string> VERAIn_XML::tokenize_string(const string & s, const char delim) const
{
  vector<string> result;

  string::size_type last_i, i;
  last_i = 0;

  while((i = s.find(delim, last_i)) != string::npos)
  {
    result.push_back(s.substr(last_i, i-last_i));
    last_i = i+1;
  }
  if (last_i < s.length()) result.push_back(s.substr(last_i));

  return(result);
}

// -------------------------------------------------------------

string VERAIn_XML::get_string_between_delims(
    const string & line,
    const char & begintag,
    const char & endtag)
{
  string result;

  string::size_type beginpos = downstring(line).find(begintag);
  string::size_type endpos = downstring(line).find(endtag);
  if (beginpos == string::npos || endpos == string::npos || endpos < beginpos) {
    return result;
  }

  beginpos ++;

  if (endpos == string::npos || beginpos > endpos) return result;

  result = trim_string(line.substr(beginpos, endpos-beginpos));
  return result;
}

// -------------------------------------------------------------

string VERAIn_XML::replace_delim_tag_with_value(
    const string & line,
    const char & begintag,
    const char & endtag,
    const map<string,double> & values_map
    )
{
  string result = line;

  string tag_string = get_string_between_delims(line, begintag, endtag);
  if( !tag_string.empty() )
  {
    vector<string> tokens = tokenize_string(tag_string, ' ');
    string tag_name = tokens[0];
    cout << "Trying to replace token = " << tag_name << endl;
    map<string,double>::const_iterator citer = values_map.find(tag_name);
    if( values_map.end() == citer )
      throw runtime_error("No value has been associated with tag \""+tag_name+"\"");

    string::size_type beginpos = downstring(line).find(begintag);
    string::size_type endpos = downstring(line).find(endtag);

    std::ostringstream sval;
    sval << citer->second;

    result.replace(beginpos, endpos-beginpos+1, sval.str());
  }

  return result;
}

// -------------------------------------------------------------

ParameterList & VERAIn_XML::get_sublist(const string & ppath, ParameterList & plist)
{
  vector<string> tokens = tokenize_string(ppath);
  if( tokens.size() > 2 )
  {
    ParameterList & next_list = plist.sublist(tokens[0]);
    return get_sublist(ppath.substr(ppath.find_first_of(".")+1), next_list);
  }
  else
    return plist.sublist(tokens[0]);
}

// -------------------------------------------------------------

ParameterList & VERAIn_XML::get_sublist(const string & ppath)
{
  return get_sublist(ppath, *param_list_);
}

// -------------------------------------------------------------

bool VERAIn_XML::is_sublist( const ParameterList & plist, const string & ppath ) const
{
  vector<string> tokens = tokenize_string(ppath);
  ParameterList next_list = plist;
  size_t i = 0;
  while( (i < tokens.size()) && next_list.isSublist(tokens[i]) )
  {
    ParameterList list2 = next_list.sublist(tokens[i]);
    next_list = list2;
    i++;
  }

  return ( i == tokens.size() );
}

// -------------------------------------------------------------

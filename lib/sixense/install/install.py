#!/usr/bin/python

import sys
import os.path
from optparse import OptionParser
from shutil import rmtree, copy, copytree
import subprocess

cmdOpts = ''
cmdArgs = ''
config = ''

menu = """
Please select your operating system:
1. Linux 64 bit
2. OSX 64 bit
"""

def is_int(s):
   try:
      int(s)
      return True
   except ValueError:
      return False


def clean_list(lst):
   if "" in lst:
      lst.remove("")
   return lst


def clean_string(string):
   string = string.lstrip()
   string = string.rstrip(" \t\r\n\0")
   return string


def force_string(value):
   if not isinstance(value, str):
      return value[0]
   else:
      return value


def get_value(key):
   return_value = []

   file = open(cmdOpts.config)
   for line in file:
      line = clean_string(line)
      if len(line) == 0:
         continue

      if line[0] == '#':
         continue

      pairs = line.split("=")

      key_file = clean_string(pairs[0])
      if key_file == key:
         for element in pairs[1].split(","):
            return_value.append(clean_string(element))
         return return_value

   return return_value


def find_in_file(filename, search_str):    # see whether a string appears in a file at all, and tell on which line
   lib_fd = open(filename,"r")
   contents = lib_fd.readlines()
   lib_fd.close()
   index = 0
   for fline in contents:
      if search_str in fline:
         return True, index
      index = index + 1
   return False, index


def append_to_file(filename, new_str):
   lib_fd = open(filename,"a")
   lib_fd.write(new_str)
   lib_fd.close()


class SDKPackager:
   def __init__(self):
      self.firstErrorAfterHeader = None
      self.versionMajor = 2
      self.versionMinor = 0
      self.versionMacro = 0
      
      self.currentDirectory = os.path.dirname(os.path.realpath(__file__))
      self.platform = ""
      
      self.linux_32 = []
      self.linux_64 = []
      self.osx = []
      self.osx64 = []
      
      print("\nSixense SDK Installation Script v%02d.%02d.%02d" % (self.versionMajor, self.versionMinor, self.versionMacro))
      if not cmdOpts.printVersionAndExit:
         print("============================================")

   def parse_config(self):
      print("-----------------------------------------------")
      print("Parsing Config File %s" % cmdOpts.config)
      print("-----------------------------------------------")
      
      self.parse_item()

   def parse_item(self):
      print("Finding Items")
      file = open(cmdOpts.config)
      
      for line in file:
         line = clean_string(line)

         if len(line) == 0:
            continue
            
         if line[0] == '#':
            continue

         pairs = line.split("=")
         key = clean_string(pairs[0])

         if key == "linux_64" and self.platform == "linux_64":
            sys.stdout.write("Found Linux 64 bit")
            sys.stdout.flush()
            for element in pairs[1].split(","):
               if len(element) > 0:
                  self.linux_64.append(clean_string(element))
            print("                             Done")
         if key == "osx_64" and self.platform == "osx_64":
            sys.stdout.write("Found OSX 64 bit")
            sys.stdout.flush()
            for element in pairs[1].split(","):
               if len(element) > 0:
                  self.osx64.append(clean_string(element))
            print("                                 Done")
               
      file.close()
      print("Done\n")

   def choose_target_platform(self):
      print(menu)
 
      response = input("Enter Selection: ")
      if response == "1":
         self.platform = "linux_64"
      elif response == "2":
         self.platform = "osx_64"
      else:
         print("Invalid Selection")
         self.choose_target_platform()
      
   def preInstall(self):
      return
      
   def install(self):
      self.copy_files_helper(self.linux_64, "Linux 64 bit")
      self.copy_files_helper(self.osx64, "OSX 64 bit")
      return

   def copy_files_helper(self, folder_list, user_text):
      if not cmdOpts.verbose: 
         self.firstErrorAfterHeader = True

      if len(folder_list) > 0:
         sys.stdout.write("- for %s\r" % user_text)
         sys.stdout.flush()
         if cmdOpts.verbose:   
            print("")
         for element in folder_list:
            destination = get_value(element + "_destination")
            source = get_value(element + "_source")
            files = get_value(element + "_file")
            source = clean_list(source)
            files = clean_list(files)
            for outfile in files:
               self.copy_file_parser(destination, source, outfile)
         if not cmdOpts.verbose:
            sys.stdout.write("%46s\r" % "Done")
            sys.stdout.write("- for %s\n" % user_text)
            sys.stdout.flush()
         else:
            print("Done\n")

   def copy_file_parser(self, dst_path, src_path, src_file):
      if not isinstance(dst_path, str):
         dst = dst_path[0]
      else:
         dst =  dst_path
      if not isinstance(src_path, str):
         src = src_path[0]
      else:
         src =  src_path

      paths_exist = True
      
      if not os.path.isdir(src):
         if self.firstErrorAfterHeader:
            print("")
            self.firstErrorAfterHeader = False
         print("Source Path Does Not Exist: %s" % src)
         paths_exist = False
      if not os.path.isdir(dst):
         if self.firstErrorAfterHeader:
            print("")
            self.firstErrorAfterHeader = False
         print("Destination Path Does Not Exist: %s" % dst)
         paths_exist = False

      if not paths_exist:
         return
         
      #copy all files
      if src_file.split('.')[0] == '*' and src_file.split('.')[1] == '*':
         for filename in os.listdir( os.path.join(".",src) ):
            self.copy_file(dst, src, filename)
      #copy all files by extension
      elif src_file.split('.')[0] == '*' and src_file.split('.')[1] != '*':
         for filename in os.listdir( os.path.join(".",src) ):
            if os.path.isfile(filename):
               if filename.split('.')[1] == src_file.split('.')[1]:
                  self.copy_file(dst, src, filename)
      #copy all files starting with <>
      elif src_file.split('.')[0] != '*' and src_file.split('.')[1] == '*':
         for filename in os.listdir( os.path.join(".",src) ):
            if filename.split('.')[0] == src_file.split('.')[0]:
               self.copy_file(dst, src, filename)
      #copy individual file
      else:
         self.copy_file(dst, src, src_file)
   
   def copy_file(self, dst_path, src_path, src_file):
      file_exists = True
         
      if not os.path.isfile(os.path.join(src_path, src_file)):
         if os.path.isdir(os.path.join(src_path, src_file)):
            if cmdOpts.verbose:
               print("Copying all files from %s to %s" % (os.path.join(src_path, src_file), dst_path))
            copytree(src_path, os.path.join(dst_path, src_file))
            return
         else:
            if self.firstErrorAfterHeader:
               print("")
               self.firstErrorAfterHeader = False
            print("Source File Does Not Exist: %s" % os.path.join(src_path, src_file))
            file_exists = False

      if not file_exists:
         return
         
      if cmdOpts.verbose:
         print("Copying File %s from %s to %s" % (src_file, src_path, dst_path))
      copy(os.path.join(src_path, src_file), dst_path)
      
   def post_install(self):
      if self.platform =="linux_32" or self.platform == "linux_64":
         config_file = force_string(get_value("linux_library_config_file"))
         lib_path = force_string(get_value("linux_library_path"))
         if os.path.isfile( config_file ):
            found, index = find_in_file(config_file,lib_path)    # is lib path already there?
            if found:
               print("Library path is already registered in %s, on line %d." % (config_file,index))
            else:
               print("Library path not registered yet. Adding library path to %s..." % config_file)
               append_to_file(config_file,"\n"+lib_path+"\n")
            lib_update_cmd = "ldconfig"
            p = subprocess.Popen(lib_update_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
         else:
            print("Unable to Find ld.so.conf")
      
   def run(self):
      self.choose_target_platform()
      self.parse_config()
      self.preInstall()
      self.install()
      self.post_install()
      
# main program starts here
if __name__ == '__main__':
   #configFile = "sdk_hierarchy_default"
   
   parser = OptionParser(usage="%prog [options]")

   parser.add_option('',"--version",
                     action="store_true",
                     dest="printVersionAndExit",
                     default=False,
                     help="Prints the version and exits",)
                     
   parser.add_option('-c',"--config",
                     action="store",
                     dest="config",
                     default="install.cfg",
                     help="Config File to use",)

   parser.add_option('-v',"--verbose",
                     action="store_true",
                     dest="verbose",
                     default=False,
                     help="Print Extra Information",)

   parser.add_option('-w',"--warning",
                     action="store_true",
                     dest="warning",
                     default=False,
                     help="Print Only Warning Information",)
                                          
   (cmdOpts, cmdArgs) = parser.parse_args()
   
   package = SDKPackager()
   
   if cmdOpts.printVersionAndExit:
      exit()
   package.run()

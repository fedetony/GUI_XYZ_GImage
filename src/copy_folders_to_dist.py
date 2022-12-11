import os, shutil, sys

def copy_folder_from_to(root_src_dir,root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.copy(src_file, dst_dir)

def extract_filename(filename,withextension=True):
    fn= os.path.basename(filename)  # returns just the name
    fnnoext, fext = os.path.splitext(fn)
    fnnoext=fnnoext.replace(fext,'')
    fn=fnnoext+fext        
    if withextension==True:
        return fn
    else:                
        return  fnnoext 

def extract_path(filename):
    fn= os.path.basename(filename)  # returns just the name
    fpath = os.path.abspath(filename)
    fpath = fpath.replace(fn,'')
    return fpath

def get_appPath():
    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)
    return application_path

def Copyfolder(file,dest):
    from_dir = get_appPath()+file    #Path/Location of the source directory
    to_dir = get_appPath()+dest+file  #Path to the destination folder
    print('My path:',get_appPath())
    print('Copy from ',file,' to ',dest+file)
    copy_folder_from_to(from_dir,to_dir)
    print(file,' Copy Done! :)')


file= os.sep+"img"
dest=os.sep+"dist"+os.sep+"GuiXYZ_V2_1"
Copyfolder(file,dest)

file= os.sep+"temp"
Copyfolder(file,dest)

file= os.sep+"macros"
Copyfolder(file,dest)

file= os.sep+"config"
Copyfolder(file,dest)


#!/usr/bin/env python
#This is the complete code for the hierarchical filesystem implemented using FUSE for the 2nd assignment. 

import logging

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn



if not hasattr(__builtins__, 'bytes'):
    bytes = str

class Memory(LoggingMixIn, Operations):
    'Example memory filesystem. Supports only one level of files.'

    def __init__(self):
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2)

    def chmod(self, path, mode):
        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        ptr['st_mode'] &= 0770000
        ptr['st_mode'] |= mode
        return 0

    def chown(self, path, uid, gid): #this is used for giving a context
        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        ptr['st_uid'] = uid
        ptr['st_gid'] = gid

    def create(self, path, mode):
        split_path = path.split('/')
        del split_path[0]
        last_element = split_path[-1]
        del split_path[-1] 
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        ptr[last_element] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                            st_size=0, st_ctime=time(), st_mtime=time(),
                            st_atime=time())
        
        #print "----"
        #print "----Updated value in 'create' function------", self.fd   #Does not return the file name

        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        #here it is searching for the path of the new file assuming it is stored as another key. Should 
        #modify it because now, the new file is in a dictionary of its parent directory. Try using split() 
        #to separate the directory names
        try:
            split_path = path.split('/')
            del split_path[0]
            ptr = self.files['/']
            for itr in split_path:
                ptr = ptr[itr] if itr != '' else ptr
                
        except KeyError:
            raise FuseOSError(ENOENT)
        
        #print "------Path in 'getattr'-------", [path]

        return ptr

    def getxattr(self, path, name, position=0):
        
        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        attrs = ptr.get('attrs', {})

        try:
            #print "------Return Value for this function-------", attrs[name]
            return attrs[name]
        except KeyError:
            #print "------Key ERROR-----Return Value for this function-------", ''
            return ''       # Should return ENOATTR

    def listxattr(self, path):

        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        attrs = ptr.get('attrs', {})
        
        return attrs.keys()

    def mkdir(self, path, mode):
        
        print "----mkdir function call----"
        print "Path - ", path
        
        split_path = path.split('/')
        del split_path[0]
        last_element = split_path[-1]
        del split_path[-1] 
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        ptr[last_element] = dict(st_mode=(S_IFDIR | mode), st_nlink=2,
                            st_size=0, st_ctime=time(), st_mtime=time(),
                            st_atime=time())

      	ptr['st_nlink'] += 1


    def open(self, path, flags):
        

        """split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr]
        """

        self.fd += 1
        #print "------Return Value for this function-------", self.fd
        #print "----------Path Opened--------------------", path
        return self.fd

    def read(self, path, size, offset, fh):
        #print "------Return Value for this function-------", self.data[path][offset:offset + size]
        return self.data[path][offset:offset + size]

    def readdir(self, path, fh):

        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        #print "+++++Self Data++++++", self.data[ptr]

        return ['.', '..'] + [x for x in ptr if x[:3] != 'st_']

    def readlink(self, path):
        return self.data[path]

    def removexattr(self, path, name):

        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        attrs = ptr.get('attrs', {})

        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR

    def rename(self, old, new):

        split_path_old = old.split('/')
        del split_path_old[0]
        last_element_old = split_path_old[-1]
        del split_path_old[-1]
        old_ptr = self.files['/']
        for itr in split_path_old:
            old_ptr = old_ptr[itr] if itr != '' else old_ptr

        split_path_new = new.split('/')
        del split_path_new[0]
        last_element_new = split_path_new[-1]
        del split_path_new[-1]
        new_ptr = self.files['/']
        for itr in split_path_new:
            new_ptr = new_ptr[itr] if itr != '' else new_ptr

        print 'Old path', old
        print 'New path', new

        new_ptr[last_element_new] = old_ptr.pop(last_element_old)
        self.data[new] = self.data[old]

    def rmdir(self, path):

        split_path = path.split('/')
        del split_path[0]
        last_element = split_path[-1]
        del split_path[-1]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        ptr.pop(last_element)

        ptr['st_nlink'] -= 1
        


        #self.files['/']['st_nlink'] -= 1

    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        print "---Entering setxattr fucntion----"
        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        attrs = ptr.setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        print "---Entering statfs fucntion----" 
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        
        print "---Entering symlink fucntion----"
        print "Target ", target
        print "Source ", source
        split_path = target.split('/')
        del split_path[0]
        last_element = split_path[-1]
        del split_path[-1]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr


        #check if ptr[target] should be ptr[last_element] 
        ptr[last_element] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1,
                                st_size=len(source))

        self.data[target] = source

    def truncate(self, path, length, fh=None):
        split_path = path.split('/')
        del split_path[0]
        last_element = split_path[-1]
        del split_path[-1]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        self.data[path] = self.data[path][:length]
        ptr['st_size'] = length

    def unlink(self, path):
        split_path = path.split('/')
        del split_path[0]
        last_element = split_path[-1]
        del split_path[-1]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        ptr.pop(last_element)

    def utimens(self, path, times=None):
        print "---Entering utimens fucntion----"
        now = time()
        atime, mtime = times if times else (now, now)

        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        ptr['st_atime'] = atime
        ptr['st_mtime'] = mtime

    def write(self, path, data, offset, fh):
        print "---Entering write fucntion----"
        split_path = path.split('/')
        del split_path[0]
        ptr = self.files['/']
        for itr in split_path:
            ptr = ptr[itr] if itr != '' else ptr

        self.data[path] = self.data[path][:offset] + data
        ptr['st_size'] = len(self.data[path])
        #print "------Return Value for this function-------", len(data)
        return len(data)


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.getLogger().setLevel(logging.DEBUG)
    fuse = FUSE(Memory(), argv[1], foreground=True, debug=True)

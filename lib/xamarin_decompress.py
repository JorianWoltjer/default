#!/usr/bin/python3
# From: https://github.com/NickstaDB/xamarin-decompress/blob/main/xamarin-decompress.py
import lz4.block
import os

def decompress_file(filename):
    fh = open(filename, "rb")
    hdr = fh.read(8)
    if hdr[:4] == "XALZ".encode("utf-8"):
        dd = fh.read()
        fh.close()
        
        dd = lz4.block.decompress(dd)
        filenameout = filename[:-3] + "decompressed" + filename[-4:]
        
        fh = open(filenameout, "wb")
        fh.write(dd)
        fh.close()
        return True
    
    return False


def decompress(target):
    success_count = 0
    
    if os.path.isfile(target):
        decompress_file(target)
    else:
        for root, dirs, files in os.walk(target):
            for filename in files:
                if filename.lower().endswith(".exe") or filename.lower().endswith(".dll"):
                    success_count += decompress_file(os.path.join(root, filename))

    return success_count

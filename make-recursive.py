#!/usr/bin/env python3
import array
import struct
import os

def read_struct(fmt,buf,offset):
    out, = struct.unpack_from(fmt,buf,offset)
    return out, offset + struct.calcsize(fmt)

class ISO(object):

    def __init__(self, path):
        with open(path, 'rb') as f:
            tmp = f.read()
            self.data = array.array('b', tmp)
        self.sector_size = 2048
        o = 0x10 * self.sector_size
        self.type,             o = read_struct('B',self.data,o)
        self.id,               o = read_struct('5s',self.data,o)
        self.version,          o = read_struct('B',self.data,o)
        _unused0,              o = read_struct('B',self.data,o)
        self.system_id,        o = read_struct('32s',self.data,o)
        self.volume_id,        o = read_struct('32s',self.data,o)
        _unused1,              o = read_struct('8s',self.data,o)
        self.volume_space_lsb, o = read_struct('<I',self.data,o)
        self.volume_space_msb, o = read_struct('>I',self.data,o)
        _unused2,              o = read_struct('32s',self.data,o)
        self.volume_set_lsb,   o = read_struct('<H',self.data,o)
        self.volume_set_msb,   o = read_struct('>H',self.data,o)
        self.volume_seq_lsb,   o = read_struct('<H',self.data,o)
        self.volume_seq_msb,   o = read_struct('>H',self.data,o)
        self.logical_block_size_lsb,   o = read_struct('<H',self.data,o)
        self.logical_block_size_msb,   o = read_struct('>H',self.data,o)
        self.path_table_size_lsb,   o = read_struct('<I',self.data,o)
        self.path_table_size_msb,   o = read_struct('>I',self.data,o)
        self.path_table_lsb,   o = read_struct('<I',self.data,o)
        self.optional_path_table_lsb,   o = read_struct('<I',self.data,o)
        self.path_table_msb,   o = read_struct('>I',self.data,o)
        self.optional_path_table_msb,   o = read_struct('>I',self.data,o)
        _offset = o
        self.root_dir_entry, o = read_struct('34s',self.data,o)

        self.root = ISOFile(self,_offset)
        self._cache = {}

    def get_file(self, path):
        if path == '/':
            return self.root
        else:
            if path in self._cache:
                return self._cache[path]
            units = path.split('/')
            units = units[1:] # remove root
            me = self.root
            for i in units:
                next_file = me.find(i)
                if not next_file:
                    me = None
                    break
                else:
                    me = next_file
            self._cache[path] = me
            return me

class ISOFile(object):

    def __init__(self, iso, offset):
        self.iso = iso
        self.offset = offset

        o = offset
        self.length,            o = read_struct('B', self.iso.data, o)
        if not self.length:
            return
        self.ext_length,        o = read_struct('B', self.iso.data, o)
        self.extent_start_lsb,  o = read_struct('<I',self.iso.data, o)
        self.extent_start_msb,  o = read_struct('>I',self.iso.data, o)
        self.extent_length_lsb, o = read_struct('<I',self.iso.data, o)
        self.extent_length_msb, o = read_struct('>I',self.iso.data, o)

        self.date_data, o = read_struct('7s', self.iso.data, o)

        self.flags, o = read_struct('b', self.iso.data, o)
        self.interleave_units, o = read_struct('b', self.iso.data, o)
        self.interleave_gap, o = read_struct('b', self.iso.data, o)

        self.volume_seq_lsb, o = read_struct('<H',self.iso.data, o)
        self.volume_seq_msb, o = read_struct('>H',self.iso.data, o)

        self.name_len, o = read_struct('b', self.iso.data, o)
        self.name, o = read_struct('{}s'.format(self.name_len), self.iso.data, o)
        self.name = self.name.decode('ascii')

    def write_extents(self):
        struct.pack_into('<I', self.iso.data, self.offset + 2, self.extent_start_lsb)
        struct.pack_into('>I', self.iso.data, self.offset + 6, self.extent_start_lsb)
        struct.pack_into('<I', self.iso.data, self.offset + 10, self.extent_length_lsb)
        struct.pack_into('>I', self.iso.data, self.offset + 14, self.extent_length_lsb)

    def readable_name(self):
        if not ';' in self.name:
            return self.name.lower()
        else:
            tmp, _ = self.name.split(';')
            return tmp.lower()


    def list(self):
        sectors = self.iso.data[self.extent_start_lsb * self.iso.sector_size: self.extent_start_lsb * self.iso.sector_size+ 3 * self.iso.sector_size]
        offset = 0

        while 1:
            f = ISOFile(self.iso, self.extent_start_lsb * self.iso.sector_size + offset)
            yield f
            offset += f.length
            if not f.length:
                break

    def find(self, name):
        sectors = self.iso.data[self.extent_start_lsb * self.iso.sector_size: self.extent_start_lsb * self.iso.sector_size+ 3 * self.iso.sector_size]
        offset = 0
        if '.' in name and len(name.split('.')[0]) > 8:
            a, b = name.split('.')
            name = a[:8] + '.' + b
        if '-' in name:
            name = name.replace('-','_')
        while 1:
            f = ISOFile(self.iso, self.extent_start_lsb * self.iso.sector_size + offset)
            if not f.length:
                if offset < self.extent_length_lsb:
                    offset += 1
                    continue
                else:
                    break
            if ';' in f.name:
                tmp, _ = f.name.split(';')
                if tmp.endswith('.'):
                    tmp = tmp[:-1]
                if tmp.lower() == name.lower():
                    return f
            elif f.name.lower() == name.lower():
                return f
            offset += f.length
        return None

image = ISO('resume.pdf')
cdfile = image.get_file('/self.pdf')

if not cdfile:
    print("No SELF.PDF?")
else:
    cdfile.extent_start_lsb = 0
    cdfile.extent_length_lsb = os.stat('resume.pdf').st_size
    cdfile.write_extents()

with open('resume.pdf','wb') as f:
    f.write(image.data)


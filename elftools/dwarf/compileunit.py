#-------------------------------------------------------------------------------
# elftools: dwarf/compileunit.py
#
# DWARF compile unit
#
# Eli Bendersky (eliben@gmail.com)
# This code is in the public domain
#-------------------------------------------------------------------------------
from .die import DIE


class CompileUnit(object):
    """ A DWARF compilation unit (CU). 
    
            A normal compilation unit typically represents the text and data
            contributed to an executable by a single relocatable object file.
            It may be derived from several source files, 
            including pre-processed "include files"
            
        Serves as a container and context to DIEs that describe objects and code
        belonging to a compilation unit.
        
        CU header entries can be accessed as dict keys from this object, i.e.
           cu = CompileUnit(...)
           cu['version']  # version field of the CU header
        
        To get the top-level DIE describing the compilation unit, call the 
        get_top_DIE method.
    """
    def __init__(self, header, dwarfinfo, structs, cu_offset, cu_die_offset):
        """ header:
                CU header for this compile unit
            
            dwarfinfo:
                The DWARFInfo context object which created this one
                        
            structs:
                A DWARFStructs instance suitable for this compile unit
            
            cu_offset:
                Offset in the stream to the beginning of this CU (its header)
            
            cu_die_offset:
                Offset in the stream of the top DIE of this CU
        """
        self.dwarfinfo = dwarfinfo
        self.header = header
        self.structs = structs
        self.cu_offset = cu_offset
        self.cu_die_offset = cu_die_offset
        
        # The abbreviation table for this CU. Filled lazily when DIEs are 
        # requested.
        self._abbrev_table = None
        
        # A list of DIEs belonging to this CU. Lazily parsed.
        self._dielist = []
        
    def get_abbrev_table(self):
        """ Get the abbreviation table (AbbrevTable object) for this CU
        """
        if self._abbrev_table is None:
            self._abbrev_table = self.dwarfinfo.get_abbrev_table(
                self['debug_abbrev_offset'])
        return self._abbrev_table

    def get_top_DIE(self):
        """ Get the top DIE (which is either a DW_TAG_compile_unit or 
            DW_TAG_partial_unit) of this CU
        """
        return self._get_DIE(0)

    def __getitem__(self, name):
        """ Implement dict-like access to header entries
        """
        return self.header[name]

    def _get_DIE(self, index):
        """ Get the DIE at the given index 
        """
        if len(self._dielist) == 0:
            self._parse_DIEs()
        return self._dielist[index]
    
    def _parse_DIEs(self):
        # Compute the boundary (one byte past the bounds) of this CU in the 
        # stream
        cu_boundary = ( self.cu_offset + 
                        self['unit_length'] + 
                        self.structs.initial_length_field_size())
        
        die_offset = self.cu_die_offset
        while die_offset < cu_boundary:
            die = DIE(cu=self, stream=self.dwarfinfo.stream, offset=die_offset)
            self._dielist.append(die)
            die_offset += die.size

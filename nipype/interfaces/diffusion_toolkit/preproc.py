# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by diffusion toolkit

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
import os
import glob
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec, OutputMultiPath, )

class DiffUnpackInputSpec(CommandLineInputSpec):
    input_dicom = File(exists=True,mandatory=True,desc='input dicom file',argstr='%s',position=1)
    out_prefix = traits.Str('output',desc='Output file prefix',argstr='%s',usedefault=True,position=2)
    output_type = traits.Enum('nii', 'analyze', 'ni1', 'nii.gz', argstr='-ot %s', desc='output file type', usedefault=True)
    split = traits.Bool(desc="""instead of saving everything in one big multi-timepoint 4D image, 
          split it into seperate files, one timepoint per file""", argstr='-split')

class DiffUnpackOutputSpec(TraitedSpec):
    converted_files = OutputMultiPath(desc='converted files')

class DiffUnpack(CommandLine):
    input_spec=DiffUnpackInputSpec
    output_spec=DiffUnpackOutputSpec

    _cmd = "diff_unpack"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        
        outputs['converted_files'] = glob.glob(os.path.abspath(self.inputs.out_prefix+'*'))
        return outputs

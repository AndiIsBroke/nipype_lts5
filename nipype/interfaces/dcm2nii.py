from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    InputMultiPath, traits, TraitedSpec,
                                    OutputMultiPath, isdefined,
                                    File, Directory)
import os
from copy import deepcopy
from nipype.utils.filemanip import split_filename
import re

class Dcm2niiInputSpec(CommandLineInputSpec):
    _xor_source = ('source_dir','source_names')
    source_dir = Directory( exist=True, argstr="%s", position=10, mandatory=True, xor=_xor_source)
    source_names = InputMultiPath(File(exists=True), argstr="%s", position=10, mandatory=True, xor=_xor_source)
    gzip_output = traits.Bool(False, argstr='-g', position=0, usedefault=True)
    nii_output = traits.Bool(True, argstr='-n', position=1, usedefault=True)
    anonymize = traits.Bool(argstr='-a', position=2)
    id_in_filename = traits.Bool(False, argstr='-i', usedefault=True, position=3)
    reorient = traits.Bool(argstr='-r', position=4)
    reorient_and_crop = traits.Bool(argstr='-x', position=5)
    output_dir = Directory(exists=True, argstr='-o %s', genfile=True, position=6)
    config_file = File(exists=True, argstr="-b %s", genfile=True, position=7)
    convert_all_pars = traits.Bool(argstr='-v', position=8)
    args = traits.Str(argstr='%s', desc='Additional parameters to the command', position=9)

class Dcm2niiOutputSpec(TraitedSpec):
    converted_files = OutputMultiPath(File(exists=True))
    reoriented_files = OutputMultiPath(File(exists=True))
    reoriented_and_cropped_files = OutputMultiPath(File(exists=True))
    bvecs = OutputMultiPath(File(exists=True))
    bvals = OutputMultiPath(File(exists=True))

class Dcm2nii(CommandLine):
    input_spec=Dcm2niiInputSpec
    output_spec=Dcm2niiOutputSpec

    _cmd = 'dcm2nii'

    def _format_arg(self, opt, spec, val):
        if opt in ['gzip_output', 'nii_output', 'anonymize', 'id_in_filename', 'reorient', 'reorient_and_crop', 'convert_all_pars']:
            spec = deepcopy(spec)
            if val:
                spec.argstr += ' y'
            else:
                spec.argstr += ' n'
                val = True
        return super(Dcm2nii, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):

        new_runtime = super(Dcm2nii, self)._run_interface(runtime)
        (self.output_files,
         self.reoriented_files,
         self.reoriented_and_cropped_files,
         self.bvecs, self.bvals) = self._parse_stdout(new_runtime.stdout)
        return new_runtime

    def _parse_stdout(self, stdout):
        files = []
        reoriented_files = []
        reoriented_and_cropped_files = []
        bvecs = []
        bvals = []
        skip = False
        last_added_file = None
        for line in stdout.split("\n"):
            if not skip:
                file = None
                if line.startswith("Saving "):
                    file = line[len("Saving "):]
                elif line.startswith("GZip..."):
                    #for gzipped outpus files are not absolute
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename('output_dir')
                    file = os.path.abspath(os.path.join(output_dir,
                                                        line[len("GZip..."):]))
                elif line.startswith("Number of diffusion directions "):
                    if last_added_file:
                        base, filename, ext = split_filename(last_added_file)
                        bvecs.append(os.path.join(base,filename + ".bvec"))
                        bvals.append(os.path.join(base,filename + ".bval"))
                elif re.search('-->(.*)', line):
                    search = re.search('.*--> (.*)', line)
                    file = search.groups()[0]

                if file:
                    files.append(file)
                    last_added_file = file
                    continue

                if line.startswith("Reorienting as "):
                    reoriented_files.append(line[len("Reorienting as "):])
                    skip = True
                    continue
                elif line.startswith("Cropping NIfTI/Analyze image "):
                    base, filename = os.path.split(line[len("Cropping NIfTI/Analyze image "):])
                    filename = "c" + filename
                    reoriented_and_cropped_files.append(os.path.join(base, filename))
                    skip = True
                    continue



            skip = False
        return files, reoriented_files, reoriented_and_cropped_files, bvecs, bvals

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['converted_files'] = self.output_files
        outputs['reoriented_files'] = self.reoriented_files
        outputs['reoriented_and_cropped_files'] = self.reoriented_and_cropped_files
        outputs['bvecs'] = self.bvecs
        outputs['bvals'] = self.bvals
        return outputs

    def _gen_filename(self, name):
        if name == 'output_dir':
            return os.getcwd()
        elif name == 'config_file':
            config_file = "config.ini"
            f = open(config_file, "w")
            # disable interactive mode
            f.write("[BOOL]\nManualNIfTIConv=0\n")
            f.close()
            return config_file
        return None

class Dcm2niixInputSpec(CommandLineInputSpec):
    source_names = InputMultiPath(File(exists=True), argstr="%s", position=-1,
                                  copyfile=False, mandatory=True, xor=['source_dir'])
    source_dir = Directory(exists=True, argstr="%s", position=-1, mandatory=True,
                           xor=['source_names'])
    out_filename = traits.Str('%t%p', argstr="-f %s", usedefault=True,
                              desc="Output filename")
    output_dir = Directory(exists=True, argstr='-o %s', genfile=True,
                           desc="Output directory")
    bids_format = traits.Bool(True, argstr='-b', usedefault=True,
                              desc="Create a BIDS sidecar file")
    compress = traits.Enum('i', ['y','i','n'], argstr='-z %s', usedefault=True,
                           desc="Gzip compress images - [y=pigz, i=internal, n=no]")
    merge_imgs = traits.Bool(False, argstr='-m', usedefault=True,
                             desc="merge 2D slices from same series")
    single_file = traits.Bool(False, argstr='-s', usedefault=True,
                              desc="Convert only one image (filename as last input")
    verbose = traits.Bool(False, argstr='-v', usedefault=True,
                          desc="Verbose output")
    crop = traits.Bool(False, argstr='-x', usedefault=True,
                       desc="Crop 3D T1 acquisitions")
    has_private = traits.Bool(False, argstr='-t', usedefault=True,
                              desc="Flag if text notes includes private patient details")


class Dcm2niixOutputSpec(TraitedSpec):
    converted_files = OutputMultiPath(File(exists=True))
    bvecs = OutputMultiPath(File(exists=True))
    bvals = OutputMultiPath(File(exists=True))
    bids = OutputMultiPath(File(exists=True))


class Dcm2niix(CommandLine):
    """Uses Chris Rorden's dcm2niix to convert dicom files
    Examples
    ========
    >>> from nipype.interfaces.dcm2nii import Dcm2niix
    >>> converter = Dcm2niix()
    >>> converter.inputs.source_names = ['functional_1.dcm', 'functional_2.dcm']
    >>> converter.inputs.compress = 'i'
    >>> converter.inputs.single_file = True
    >>> converter.inputs.output_dir = '.'
    >>> converter.cmdline # doctest: +SKIP
    'dcm2niix -b y -z i -x n -t n -m n -f %t%p -o . -s y -v n functional_1.dcm'
    >>> flags = '-'.join([val.strip() + ' ' for val in sorted(' '.join(converter.cmdline.split()[1:-1]).split('-'))])
    >>> flags # doctest: +ALLOW_UNICODE
    ' -b y -f %t%p -m n -o . -s y -t n -v n -x n -z i '
    """

    input_spec = Dcm2niixInputSpec
    output_spec = Dcm2niixOutputSpec
    _cmd = 'dcm2niix'

    def _format_arg(self, opt, spec, val):
        if opt in ['bids_format', 'merge_imgs', 'single_file', 'verbose', 'crop',
                   'has_private']:
            spec = deepcopy(spec)
            if val:
                spec.argstr += ' y'
            else:
                spec.argstr += ' n'
                val = True
        if opt == 'source_names':
            return spec.argstr % val[0]
        return super(Dcm2niix, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        new_runtime = super(Dcm2niix, self)._run_interface(runtime)
        if self.inputs.bids_format:
            (self.output_files, self.bvecs,
             self.bvals, self.bids) = self._parse_stdout(new_runtime.stdout)
        else:
             (self.output_files, self.bvecs,
             self.bvals) = self._parse_stdout(new_runtime.stdout)
        return new_runtime

    def _parse_stdout(self, stdout):
        files = []
        bvecs = []
        bvals = []
        bids = []
        skip = False
        find_b = False
        for line in stdout.split("\n"):
            if not skip:
                out_file = None
                if line.startswith("Convert "): # output
                    fname = str(re.search('\S+/\S+', line).group(0))
                    if isdefined(self.inputs.output_dir):
                        output_dir = self.inputs.output_dir
                    else:
                        output_dir = self._gen_filename('output_dir')
                    out_file = os.path.abspath(os.path.join(output_dir, fname))
                    # extract bvals
                    if find_b:
                        bvecs.append(out_file + ".bvec")
                        bvals.append(out_file + ".bval")
                        find_b = False
                # next scan will have bvals/bvecs
                elif 'DTI gradients' in line or 'DTI gradient directions' in line:
                    find_b = True
                else:
                    pass
                if out_file:
                    if self.inputs.compress == 'n':
                        files.append(out_file + ".nii")
                    else:
                        files.append(out_file + ".nii.gz")
                    if self.inputs.bids_format:
                        bids.append(out_file + ".json")
                    continue
            skip = False
        # just return what was done
        if not bids:
            return files, bvecs, bvals
        else:
            return files, bvecs, bvals, bids

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['converted_files'] = self.output_files
        outputs['bvecs'] = self.bvecs
        outputs['bvals'] = self.bvals
        if self.inputs.bids_format:
            outputs['bids'] = self.bids
        return outputs

    def _gen_filename(self, name):
        if name == 'output_dir':
            return os.getcwd()
        return None

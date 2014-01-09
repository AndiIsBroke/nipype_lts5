# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""

from nipype.interfaces.base import (BaseInterface, BaseInterfaceInputSpec, traits,
                                    File, TraitedSpec, Directory, OutputMultiPath)
import os, os.path as op
from nipype.utils.misc import package_check
import warnings

from ... import logging
iflogger = logging.getLogger('interface')

#have_cmtk = True
#try:
#    package_check('cmtklib')
#except Exception, e:
#    have_cmtk = False
#    warnings.warn('cmtklib not installed')
#else:
from cmtklib.parcellation import (get_parcellation, create_annot_label, 
                                 create_roi, create_wm_mask,
                                 crop_and_move_datasets, generate_WM_and_GM_mask,
                                 crop_and_move_WM_and_GM)

class ParcellateInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(desc='Freesurfer main directory')
    subject_id = traits.String(mandatory=True, desc='Subject ID')
    parcellation_scheme = traits.Enum('Lausanne2008',['Lausanne2008','NativeFreesurfer'], usedefault = True)


class ParcellateOutputSpec(TraitedSpec):
    #roi_files = OutputMultiPath(File(exists=True),desc='Region of Interest files for connectivity mapping')
    white_matter_mask_file = File(desc='White matter mask file')
    #cc_unknown_file = File(desc='Image file with regions labelled as unknown cortical structures',
    #                exists=True)
    #ribbon_file = File(desc='Image file detailing the cortical ribbon',
    #                exists=True)
    #aseg_file = File(desc='Automated segmentation file converted from Freesurfer "subjects" directory',
    #                exists=True)
    roi_files_in_structural_space = OutputMultiPath(File(exists=True),
                                desc='ROI image resliced to the dimensions of the original structural image')


class Parcellate(BaseInterface):
    """Subdivides segmented ROI file into smaller subregions

    This interface interfaces with the ConnectomeMapper Toolkit library
    parcellation functions (cmtklib/parcellation.py) for all
    parcellation resolutions of a given scheme.

    Example
    -------

    >>> import nipype.interfaces.cmtk as cmtk
    >>> parcellate = cmtk.Parcellate()
    >>> parcellate.inputs.subjects_dir = '.'
    >>> parcellate.inputs.subject_id = 'subj1'
    >>> parcellate.run()                 # doctest: +SKIP
    """

    input_spec = ParcellateInputSpec
    output_spec = ParcellateOutputSpec

    def _run_interface(self, runtime):
        #if self.inputs.subjects_dir:
        #   os.environ.update({'SUBJECTS_DIR': self.inputs.subjects_dir})
        iflogger.info("ROI_HR_th.nii.gz / fsmask_1mm.nii.gz CREATION")
        iflogger.info("=============================================")
        
        if self.inputs.parcellation_scheme == "Lausanne2008":
            create_annot_label(self.inputs.subject_id, self.inputs.subjects_dir)
            create_roi(self.inputs.subject_id, self.inputs.subjects_dir)
            create_wm_mask(self.inputs.subject_id, self.inputs.subjects_dir)
            crop_and_move_datasets(self.inputs.subject_id, self.inputs.subjects_dir)
        if self.inputs.parcellation_scheme == "NativeFreesurfer":
            generate_WM_and_GM_mask(self.inputs.subject_id, self.inputs.subjects_dir)
            crop_and_move_WM_and_GM(self.inputs.subject_id, self.inputs.subjects_dir)
            
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        
        outputs['white_matter_mask_file'] = op.abspath('fsmask_1mm.nii.gz')
        #outputs['cc_unknown_file'] = op.abspath('cc_unknown.nii.gz')
        #outputs['ribbon_file'] = op.abspath('ribbon.nii.gz')
        #outputs['aseg_file'] = op.abspath('aseg.nii.gz')
        
        #outputs['roi_files'] = self._gen_outfilenames('ROI_HR_th')
        outputs['roi_files_in_structural_space'] = self._gen_outfilenames('ROIv_HR_th')

        return outputs

    def _gen_outfilenames(self, basename):
        filepaths = []
        for scale in get_parcellation(self.inputs.parcellation_scheme).keys():
            filepaths.append(op.abspath(basename+'_'+scale+'.nii.gz'))
        return filepaths
        

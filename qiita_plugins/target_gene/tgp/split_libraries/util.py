# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, exists
from functools import partial
from os import makedirs, stat

import pandas as pd
from h5py import File
# Currently the EBI submission is not part of the target gene plugin
# and the demux file is not its own project, so we need to import from
# qiita_ware. Plans are to the EBI submission to the target gene plugin
from qiita_ware.demux import to_hdf5


def get_artifact_information(qclient, artifact_id):
    """Retrieves the artifact information for running split libraries

    Parameters
    ----------
    qclient : tgp.qiita_client.QiitaClient
        The Qiita server client
    artifact_id : str
        The artifact id

    Returns
    -------
    list of (str, str), str, str
        The artifact filepaths and their type
        The artifact mapping file
        The artifact type

    Raises
    ------
    ValueError
        If there is any problem gathering the information from the server
    """
    # Get the artifact filepath information
    fps_info = qclient.get("/qiita_db/artifacts/%s/filepaths/" % artifact_id)
    fps = fps_info['filepaths']

    # Get the artifact metadata
    metadata_info = qclient.get(
        "/qiita_db/artifacts/%s/mapping/" % artifact_id)
    mapping_file = metadata_info['mapping']

    # Get the artifact type
    type_info = qclient.get("/qiita_db/artifacts/%s/type/" % artifact_id)
    artifact_type = type_info['type']

    return fps, mapping_file, artifact_type


def split_mapping_file(mapping_file, out_dir):
    """Splits a QIIME-compliant mapping file by run_prefix

    Parameters
    ----------
    mapping_file : str
        The mapping file filepath
    out_dir : str
        The path to the output directory

    Returns
    -------
    list of str
        The paths to the splitted mapping files
    """
    mf = pd.read_csv(mapping_file, delimiter='\t', dtype=str, encoding='utf-8')
    mf.set_index('#SampleID', inplace=True)

    path_builder = partial(join, out_dir)
    if 'run_prefix' in mf:
        if not exists(out_dir):
            makedirs(out_dir)
        output_fps = []
        for prefix, df in mf.groupby('run_prefix'):
            out_fp = path_builder('%s_mapping_file.txt' % prefix)
            output_fps.append(out_fp)
            df.to_csv(out_fp, index_label='#SampleID', sep='\t',
                      encoding='utf-8')
    else:
        output_fps = [mapping_file]

    return output_fps


def generate_demux_file(sl_out):
    """Creates the HDF5 demultiplexed file

    Parameters
    ----------
    sl_out : str
        Path to the output directory of split libraries

    Returns
    -------
    str
        The path of the demux file

    Raises
    ------
    ValueError
        If the split libraries output does not contain the demultiplexed fastq
        file
    """
    fastq_fp = str(join(sl_out, 'seqs.fastq'))
    if not exists(fastq_fp):
        raise ValueError("The split libraries output directory does not "
                         "contain the demultiplexed fastq file.")
    elif stat(fastq_fp).st_size == 0:
        raise ValueError("No sequences were demuxed. Check your parameters.")

    demux_fp = join(sl_out, 'seqs.demux')
    with File(demux_fp, "w") as f:
        to_hdf5(fastq_fp, f)
    return demux_fp


def generate_artifact_info(sl_out):
    """Creates the artifact information to attach to the payload

    Parameters
    ----------
    sl_out : str
        Path to the split libraries output directory

    Returns
    -------
    list of [str, str, list of (str, str)]
        The artifacts information to include in the payload when the split
        libraries job is completed.
        - The command output name
        - The artifact type
        - The list of filepaths with their artifact type
    """
    path_builder = partial(join, sl_out)
    filepaths = [(path_builder('seqs.fna'), 'preprocessed_fasta'),
                 (path_builder('seqs.fastq'), 'preprocessed_fastq'),
                 (path_builder('seqs.demux'), 'preprocessed_demux'),
                 (path_builder('split_library_log.txt'), 'log')]
    return [['demultiplexed', 'Demultiplexed', filepaths]]

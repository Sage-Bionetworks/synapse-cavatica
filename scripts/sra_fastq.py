"""Source from https://erilu.github.io/python-fastq-downloader/
"""
from io import StringIO
import os
import subprocess

import GEOparse
import synapseclient
import pandas as pd


def main():
    """Download FASTQ from GEO and upload into Synapse"""
    syn = synapseclient.login()

    gse_ids = ["GSE79842", "GSE84531", "GSE128622", "GSE167124"]
    # private_gse_id = ["GSE190125"]
    srr_ids = []
    # Get all SRR ids
    for gse_id in gse_ids:
        get_srr_cmd = ["pysradb", "gsm-to-srr", gse_id]
        srr_data = subprocess.run(
            get_srr_cmd, check=True, capture_output=True, encoding='utf-8'
        )
        # Replace space with \t to read it in with pandas
        srr_data_io = StringIO(srr_data.stdout.replace(" ", "\t"))
        srr_df = pd.read_csv(srr_data_io, sep="\t")
        srr_ids.extend(srr_df['run_accession'].tolist())

    # this will download the .sra files to cwd as sra_id/...
    # (will create directory if not present)
    for sra_id in srr_ids:
        # prefetch --type fastq SRR11180057
        print(f"Currently downloading: {sra_id}", flush=True)
        prefetch_cmd = ["prefetch", sra_id]
        print(f"The command used was: {' '.join(prefetch_cmd)}", flush=True)
        subprocess.run(prefetch_cmd, check=True)
        # Store SRA file into Synapse
        # syn.store(synapseclient.File(f"{sra_id}/{sra_id}.sra", parent="syn26140285"))

        print(f"Generating fastq for: {sra_id}", flush=True)
        fastq_dump_cmd = ['fasterq-dump', sra_id, '-O', sra_id]
        print(f"The command used was: {' '.join(fastq_dump_cmd)}", flush=True)
        subprocess.run(fastq_dump_cmd, check=True)

        # Add fastq files
        fastq_files = os.listdir('fastq')
        for fastq in fastq_files:
            fastq_path = os.path.join('fastq', fastq)
            gzip_cmd = ['gzip', fastq_path]
            print(" ".join(gzip_cmd), flush=True)
            subprocess.check_call(gzip_cmd)
            print("Storing file", flush=True)
            syn.store(
                synapseclient.File(f"{fastq_path}.gz", parent="syn26140163")
            )
            os.remove(f"{fastq_path}.gz")
        os.remove(f"{sra_id}/{sra_id}.sra")


def annotation():
    syn = synapseclient.login()
    gse_ids = ["GSE79842", "GSE84531", "GSE128622", "GSE167124"]
    # private_gse_id = ["GSE190125"]
    # Get all SRR ids
    for gse_id in gse_ids:
        get_srr_cmd = ["pysradb", "gsm-to-srr", gse_id]
        srr_data = subprocess.run(
            get_srr_cmd, check=True, capture_output=True, encoding='utf-8'
        )
        # Replace space with \t to read it in with pandas
        srr_data_io = StringIO(srr_data.stdout.replace(" ", "\t"))
        srr_df = pd.read_csv(srr_data_io, sep="\t")

        for _, row in srr_df.iterrows():
            gsm_id = row['experiment_alias']
            sra_id = row['run_accession']
            annotation = {
                "gse_id": gse_id,
                "gsm_id": gsm_id,
                "sra_id": sra_id
            }
            # Get GSM
            gsm = GEOparse.get_GEO(geo=gsm_id, destdir="./.data")
            gsm_metadata = gsm.metadata
            keys_transform = {
                'source_name_ch1': "source_name",
                'organism_ch1': 'organism',
                'platform_id': 'platform_id',
                'instrument_model': 'instrument_model',
                'library_selection': 'library_selection',
                'library_source': 'library_source',
                'library_strategy': 'library_strategy',
                'title': 'specimen_id'
            }
            for key, value in keys_transform.items():
                annotation[value] = gsm_metadata[key][0]
            if annotation['specimen_id'].startswith("HTP"):
                annotation['patient_id'] = "HTP"
            else:
                annotation['patient_id'] = "cell line"

            fastq_files = syn.tableQuery(
                f"select id from syn26852141 where name like '{sra_id}%'"
            )
            fastq_files_df = fastq_files.asDataFrame()
            for syn_id in fastq_files_df['id']:
                ent = syn.get(syn_id, downloadFile=False)
                ent.annotations.update(annotation)
                ent.s3_path = f"s3://kf-strides-study-us-east-1-prd-sd-z6mwd3h0/source/htp-rna/{ent.name}"
                syn.store(ent)


if __name__ == "__main__":
    main()

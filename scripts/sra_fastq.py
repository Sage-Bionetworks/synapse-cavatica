"""Source from https://erilu.github.io/python-fastq-downloader/
"""
import os
import subprocess

import synapseclient


def main():

    syn = synapseclient.login()
    # Get SRA files
    geo_files_synid = "syn25909695"
    sra_files = syn.getChildren(geo_files_synid)
    sra_numbers = []
    for sra_file in sra_files:
        ent = syn.get(sra_file['id'], downloadFile=False)
        # Get SRA number
        sra_numbers.append(ent._file_handle['fileName'].replace(".sra", ''))

    # this will download the .sra files to cwd as sra_id/...
    # (will create directory if not present)
    for sra_id in sra_numbers:
        print(f"Currently downloading: {sra_id}")
        prefetch_cmd = ["prefetch", sra_id]
        print(f"The command used was: {' '.join(prefetch_cmd)}")
        subprocess.check_call(prefetch_cmd)
        # Store SRA file into Synapse
        # syn.store(synapseclient.File(f"{sra_id}/{sra_id}.sra", parent="syn26140285"))

    # this will extract the .sra files from above into a folder named 'fastq'
    for sra_id in sra_numbers:
        print(f"Generating fastq for: {sra_id}")
        # fastq_dump_cmd = [
        #     "fastq-dump", "--outdir", "fastq", "--gzip",
        #     "--skip-technical", "--readids", "--read-filter", "pass",
        #     "--dumpbase", "--split-3",
        #     "--clip", f"{sra_id}/{sra_id}.sra"
        # ]
        fastq_dump_cmd = ['fasterq-dump', sra_id, '-O', 'fastq']
        print(f"The command used was: {' '.join(fastq_dump_cmd)}")

    # Add fastq file
    fastq_files = os.listdir('fastq')
    for fastq in fastq_files:
        fastq_path = os.path.join('fastq', fastq)
        gzip_cmd = ['gzip', fastq_path]
        print(" ".join(gzip_cmd))
        subprocess.check_call(gzip_cmd)
        print("Storing file")
        syn.store(
            synapseclient.File(f"{fastq_path}.gz", parent="syn26140163")
        )
        os.remove(f"{fastq_path}.gz")

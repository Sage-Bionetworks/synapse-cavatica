"""Source from https://erilu.github.io/python-fastq-downloader/
"""
import os
import subprocess

import synapseclient


def main():
    """Download FASTQ from GEO and upload into Synapse"""
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
        print(f"Currently downloading: {sra_id}", flush=True)
        prefetch_cmd = ["prefetch", sra_id]
        print(f"The command used was: {' '.join(prefetch_cmd)}", flush=True)
        subprocess.check_call(prefetch_cmd)
        # Store SRA file into Synapse
        # syn.store(synapseclient.File(f"{sra_id}/{sra_id}.sra", parent="syn26140285"))

        print(f"Generating fastq for: {sra_id}", flush=True)
        fastq_dump_cmd = ['fasterq-dump', sra_id, '-O', 'fastq']
        print(f"The command used was: {' '.join(fastq_dump_cmd)}", flush=True)
        subprocess.check_call(fastq_dump_cmd)

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


if __name__ == "__main__":
   main()

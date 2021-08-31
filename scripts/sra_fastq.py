"""Source from https://erilu.github.io/python-fastq-downloader/
"""
import subprocess


sra_numbers = [
    "SRR3322281"
]

# this will download the .sra files to cwd as sra_id/...
# (will create directory if not present)
for sra_id in sra_numbers:
    print(f"Currently downloading: {sra_id}")
    prefetch_cmd = ["prefetch", sra_id]
    print(f"The command used was: {' '.join(prefetch_cmd)}")
    subprocess.check_call(prefetch_cmd)

# this will extract the .sra files from above into a folder named 'fastq'
for sra_id in sra_numbers:
    print(f"Generating fastq for: {sra_id}")
    fastq_dump_cmd = [
        "fastq-dump", "--outdir", "fastq", "--gzip",
        "--skip-technical", "--readids", "--read-filter", "pass",
        "--dumpbase", "--split-3",
        "--clip", f"{sra_id}/{sra_id}.sra"
    ]
    print(f"The command used was: {' '.join(fastq_dump_cmd)}")
    subprocess.check_call(fastq_dump_cmd)
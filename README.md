# synapse-cavatica
This repository will house code that assists with the integration between Synapse and CAVATICA.


## Synapse - CAVATICA Task
This is a a proof-of-concept flow for some RNA-seq data using this [KF RNA-Seq workflow](https://github.com/kids-first/kf-rnaseq-workflow) ([Link on CAVATICA](https://cavatica.sbgenomics.com/public/apps#cavatica/apps-publisher/kfdrc-rnaseq-workflow/)). Here are the high level steps:

1. RNA-seq data files [FASTQ] and metadata [annotations/CSV] indexed in Synapse, stored in S3
1. Manual submission that couples synapseclient and CAVATICA API
1. Semi-automated submission using Synapse Evaluation API or AWS Lambda
1. Execution of processing workflow [CWL] in CAVATICA environment
    - if there should be status updates back to Synapse (e.g. 58% of processing is done)
1. Return of results [BAMs, TSVs] to Synapse, or elsewhere.

More details of this task can be found [here](https://github.com/include-dcc/stwg-issue-tracking/issues/7)

## Synapse - CAVATICA Shiny
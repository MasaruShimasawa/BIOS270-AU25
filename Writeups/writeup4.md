1. How could one add a differential expression analysis (DESeq2) step 
to the rnaseq_pipeline_array_depend.sh script such that DESeq2 runs 
only after all salmon jobs for all samples have completed? 
(No code required - describe conceptually)
    When submitting DESeq2 job, use --dependency=afterok:$SALMONJOB_ID

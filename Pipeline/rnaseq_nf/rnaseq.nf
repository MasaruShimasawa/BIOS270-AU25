// RNA-seq QC → Trim Galore → Salmon + DESeq2 (from CSV samplesheet)
// Expect a CSV with columns: sample,read1,read2,condition
// No intermediate samples.csv is generated; DESeq2 infers quant.sf paths
// from --outdir/<sample>/salmon_outs/quant.sf
nextflow.enable.dsl=2

include { FASTQC } from './modules/qc/fastqc.nf'
include { TRIMGALORE } from './modules/qc/trimgalore.nf'
include { SALMON } from './modules/pseudoalign/salmon.nf'
include { DESEQ2 } from './modules/diffexp/deseq2.nf'

// -------------------- NEW PROCESS: SALMON INDEX --------------------
// This process builds the Salmon index from a reference transcriptome FASTA file.
process SALMON_INDEX {
    publishDir "${params.outdir}/salmon_index", mode: 'copy'

    input:
    path transcriptome_fasta  // Input transcriptome FASTA file

    output:
    path "salmon_index_dir"   // Output index directory

    script:
    """
    salmon index -t ${transcriptome_fasta} -i salmon_index_dir
    """
}


// -------------------- Channels --------------------
def samplesheet_ch = Channel
    .fromPath(params.samplesheet)
    .ifEmpty { error "Missing --samplesheet file: ${params.samplesheet}" }

samples_ch = samplesheet_ch.splitCsv(header:true).map { row ->
    tuple(row.sample.trim(), file(row.read1.trim(), absolute: true), file(row.read2.trim(), absolute:true), row.condition.trim())
}


// -------------------- Workflow --------------------

workflow {

    // 1. **Index Preparation Logic (Conditional execution)**

    Channel index_path_ch

    if (params.index) {
        // Case 1: Existing index provided. Use it directly.
        index_path_ch = Channel.value( file(params.index) )
    }
    else if (params.transcriptome) {
        // Case 2: Transcriptome FASTA provided. Build the index.
        log.info "No index provided. Running SALMON_INDEX using: ${params.transcriptome}"

        fasta_ch = Channel.value( file(params.transcriptome) )

        // Run the indexing process
        SALMON_INDEX(fasta_ch)

        // Assign the output channel from the process
        index_path_ch = SALMON_INDEX.out
    }
    else {
        // Case 3: Error
        error "Configuration Error: You must provide either 'params.index' or 'params.transcriptome'."
    }

    // --------------------------------------------------------------------------------------

    // 2. **QC and Trimming**
    FASTQC(samples_ch)
    trimmed_ch = TRIMGALORE(samples_ch)

    // 3. **Quantification**

    // Pass the index path channel to SALMON, combining the multiple read samples
    // This is the CRUCIAL point for dependency and resource sharing.
    quant_ch = SALMON(trimmed_ch.combine(index_path_ch))

    // 4. **Differential Expression Analysis (DESeq2)**

    if( params.run_deseq ) {
        // Collect all Salmon outputs into a single CSV file.
        quant_paths_ch = quant_ch
            // Assuming quant_ch emits: (sample, quant_path, condition)
            .map { sample, quant, cond -> "${sample},${quant}" }
            .collectFile(
                name: "quant_paths.csv",
                newLine: true,
                seed: "sample,quant_path"
            )

        // Run DESeq2
        DESEQ2(quant_paths_ch, samplesheet_ch)
    }
}

workflow.onComplete {
    log.info "Pipeline finished. Results in: ${params.outdir}"
}

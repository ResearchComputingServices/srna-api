from Bio.Blast import NCBIXML
from Bio.Blast.Applications import NcbiblastnCommandline

import io

class Blast:

    def blast(self, query_file, subject_file, query_str, e_cutoff, identity_perc_cutoff):
        output = NcbiblastnCommandline(query=query_file, subject=subject_file, evalue=e_cutoff, perc_identity=identity_perc_cutoff*100, outfmt=5, task="blastn-short")()[0]
        blast_result_record = NCBIXML.read(io.StringIO(output))
        list_hits = []

        for alignment in blast_result_record.alignments:
            for hsp in alignment.hsps:
                 list_hits.append(hsp)

        return (list_hits)
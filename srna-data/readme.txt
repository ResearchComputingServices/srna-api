blastn -query seq_sRNA.fasta -subject seq_Source.fasta -outfmt 6 -task 'blastn-short' -evalue 0.01 -perc_identity 80 > blast.out

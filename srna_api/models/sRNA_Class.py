from Bio.Seq import Seq
from Bio.Alphabet import IUPAC

class sRNA_Class:
    input_sequence = Seq("", IUPAC.unambiguous_dna)   #The original input genome from which the sRNA is derived.
    input_record = 0
    start_position_sRNA = 0 #The start position of the sRNA in the genome
    end_position_sRNA = 0 #The end position of the sRNA in the genome
    length_sRNA = 0
    sequence_sRNA = Seq("", IUPAC.unambiguous_dna) #The sRNA sequence
    start_position_CDS = 0 #The start position of the CDS from which the sRNA was computed
    end_position_CDS = 0  #The end position of the CDS from which the sRNA was computed
    shift = 0   #Shift position to compute sRNA
    strand = 0  #The strand 1=forward and -1=backward of the CDS
    gene = ''   #Gene tag from the CDS
    locus_tag=''  #Locus tag
    list_hits = []



    def __init__(self, start_position_sRNA=0, end_position_sRNA=0, length_sRNA=0, sequence_sRNA=Seq(""), start_position_CDS=0, end_position_CDS=0, shift=0, strand=0, gene='', locus_tag=''):
        self.start_position_sRNA = start_position_sRNA
        self.end_position_sRNA = end_position_sRNA
        self.length_sRNA = length_sRNA
        self.sequence_sRNA = sequence_sRNA
        self.start_position_CDS = start_position_CDS
        self.end_position_CDS = end_position_CDS
        self.shift = shift
        self.strand = strand
        self.gene = gene
        self.locus_tag = locus_tag






















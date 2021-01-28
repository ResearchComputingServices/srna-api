from Bio.Seq import Seq
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio import Entrez
from Bio.SeqFeature import SeqFeature, FeatureLocation
import sys
import traceback
from srna_api.models.sRNA_Class import sRNA_Class
from srna_api.providers.blast import Blast
import pandas as pd
from io import BytesIO
import json
import os.path
from datetime import datetime
from io import StringIO
import uuid

Entrez.email = "jazminromero@cunet.carleton.ca"  # Always tell NCBI who you are


class sRNA_Provider:

    blastProvider = Blast()


    #Fetch a sequence from Entrez database given an accesssion number
    #Save it in base_directory location
    #Parse the sequence and returns a list of seq_records
    def fetch_and_save_input_sequence(self, accession, base_directory):
        filename = base_directory + '/' + accession + ".gbk"
        if not os.path.isfile(filename):
            # Downloads and save sequence
            net_handle = Entrez.efetch(
                db="nucleotide", id=accession, rettype="gb", retmode="text"
            )
            out_handle = open(filename, "w")
            out_handle.write(net_handle.read())
            out_handle.close()
            net_handle.close()
            print("Saved")

        print("Parsing...")
        seq_iterator = SeqIO.parse(filename, "genbank")
        seq_record_list = list(seq_iterator)
        return seq_record_list


    # Fetch a sequence from Entrez database given an accesssion number
    # Parse the sequence and returns a list of seq_records
    def fetch_input_sequence(self, accession):
        try:
            # Download sequence
            handle = Entrez.efetch(db="nucleotide", id=accession, rettype="gb", retmode="text")
            seq_iterator = SeqIO.parse(handle, "genbank")
            seq_record_list = list(seq_iterator)
        except:
            seq_record_list = []
            print("Unexpected error at fetch_input_sequence:", sys.exc_info()[0])
            traceback.print_exc()

        return seq_record_list


    #Creates a handle from a string and return a list of seq_record
    def read_input_sequence_create_handle(self, sequence_to_read, format):
        try:
            #Create a handle from the string sequence_to_read
            handle = StringIO(sequence_to_read)
            seq_iterator = SeqIO.parse(handle, format)

            seq_record_list = list(seq_iterator)
        except Exception as e:
            seq_record_list=[]
            print("Unexpected error at read_sequence:", sys.exc_info()[0])
            traceback.print_exc()

        return seq_record_list


    #Reads a file and return a list of seq_record
    def read_input_sequence(self, input_file, format):
        try:
            seq_iterator = SeqIO.parse(input_file,format)
            seq_record_list = list(seq_iterator)
        except Exception as e:
            seq_record_list=[]
            print("Unexpected error at read_sequence:", sys.exc_info()[0])
            traceback.print_exc()

        return seq_record_list

    #Given an excel file with a specific structure
    #First column should contain the heading Gene_Tag
    #Second column should contain the heading Locus_Tag
    #Returns the list of gene and locus tags
    def load_locus_gene_tags(self, file_name):
        try:
            gene_tags = []
            locus_tags = []

            df = pd.read_excel(file_name)
            gene_tags_input = df['Gene_Tag'].values.tolist()
            locus_tags_input = df['Locus_Tag'].values.tolist()

            for tag in gene_tags_input:
                if str(tag) != 'nan':
                    gene_tags.append(tag)

            for tag in locus_tags_input:
                if str(tag) != 'nan':
                    locus_tags.append(tag)

        except:
            print("Unexpected error at load_locus_gene_tags:", sys.exc_info()[0])
            traceback.print_exc()

        return gene_tags, locus_tags



    #Returns a list of seq_records
    #Either by processing a file (priority 1) or by a downloading a sequence from entrez
    #given an accession number (priority 2)
    def load_input_sequence(self, sequence_to_read, accession_number, format):
        sequence_record_list = []
        # 1.1 Read an attached sequence file
        if sequence_to_read:
            # Read file_sequence
            sequence_record_list = self.read_input_sequence(sequence_to_read, format)
        else:
            # 1.2 Fetch the sequence in Entrez database using accession number
            if accession_number:
                # Fetch the sequence using accession number
                sequence_record_list = self.fetch_input_sequence(accession_number)

        return sequence_record_list




    #Prints a seq_record
    def __print_seq_record(self, seq_record):
        print('Record ID: ', seq_record.id)
        # repr is a "representative" output of the sequence
        print('Sequence: ', repr(seq_record.seq))
        print('Sequence Length:', "{:,}".format(len(seq_record)))
        # print ('Annotations: ', seq_record.annotations)
        #print('\n')


    #Print a list of sequences
    def print_input_sequence(self, seq_record_list):
        try:
            count = 0
            for seq_record in seq_record_list:
                self. __print_seq_record(seq_record)
                count = count + 1

            print('\nTotal Records: ', count)
        except:
            print("Unexpected error at print_sequence:", sys.exc_info()[0])
            traceback.print_exc()



    def __sign(self, number):
        if number>0:
            return '+'
        else:
            if number <0:
                return '-'
            else:
                return ' '

        # Python sequence start at 0 to end-1
        # However when we obtain a substring from a string the method is [start...end)
        # That is end is not inclusive
        # Therefore a start position in the file is position+1
        # But end position remains the same, because an end position actually is end-1 in python
        # python sequence
        # [start...end)
        # file sequence
        # [start+1...end]

    def _start_in_file(self, position):
        return position + 1



    def _end_in_file(self, position):
        return position



    def total_srnas(self, list_srna):
        total = 0
        for list in list_srna:
            total = total + len(list)
        return total



    def __print_srna(self, srna):
        print ('sRNA: ',srna.sequence_sRNA)


        print ('sRNA location: ['+str("{:,}".format(self._start_in_file(srna.start_position_sRNA))) + ' - ' + str("{:,}".format(srna.end_position_sRNA)) + ']')
        print ('sRNA Length: ',srna.length_sRNA)
        print ('CDS: [' + str("{:,}".format(self._start_in_file(srna.start_position_CDS))) + '-' + str("{:,}".format(srna.end_position_CDS)) + '] (' + self.__sign(srna.strand) + ')')
        if srna.gene!='':
            print ('Info: ', srna.gene)

        print('\n')

        if len(srna.list_hits)>0:
            print ('Total Hits: ',len(srna.list_hits))
            print ("Hit# \t\t Expect Value \t Per. Id. \t Align Length \t Hit Start - Hit End")
            for index, hit in enumerate(srna.list_hits):
                if srna.strand>0:
                    print(str(index+1) + "\t\t\t" + str(hit.expect) + "\t \t" + str((hit.score / srna.length_sRNA) * 100) + "\t \t" + str(
                    hit.align_length) + "\t \t" + "[" + str("{:,}".format(hit.sbjct_end)) + "-" + str(
                    "{:,}".format(hit.sbjct_start)) + "]")
                else:
                    print(str(index+1)  + "\t\t\t" + str(hit.expect) + "\t\t \t" + str((hit.score/srna.length_sRNA)*100) + "\t \t" + str(hit.align_length) + "\t \t \t" + "[" + str("{:,}".format(hit.sbjct_start)) + "-" + str("{:,}".format(hit.sbjct_end)) + "]")
        else:
            print ('No hits found.')

        print('\n')


    def __print_list_srna(self, list_sRNA):
        for index, srna in enumerate(list_sRNA):
                print ('\n')
                print("sRNA #" + str(index + 1))
                self.__print_srna(srna)



    def print_list_srna(self, list_sRNA, seq_record_list):
        for record_index, list_sRNA_per_record in enumerate(list_sRNA):
                print('----------------------------------------------------------------------------')
                print ("Record: # ", record_index+1)
                self.__print_seq_record(seq_record_list[record_index])
                print ('Total sRNAs: ', len(list_sRNA_per_record))
                self.__print_list_srna(list_sRNA_per_record)



    #Computes an sRNA for a CDS that is encoded forward
    def sRNA_Forward(self, sequence, start_CDS, end_CDS, strand, gene, locus_tag, position, length):
        sRNA = sRNA_Class()
        try:

            shift = position
            start_gene = start_CDS

            #There is no 0 position
            #-1 is the position immediately before the start of the gene
            #+1 is the first position in the gene
            #Therefore if +1 the position is actually start_gene
            if position > 0:
                shift = shift - 1

            mid_position = start_gene + shift
            half_length =  int((length-1)//2)    #We substract -1 due to the mid_position
            start_sRNA_position = mid_position - half_length
            end_sRNA_position = start_sRNA_position + length

            if start_sRNA_position<0:
                start_sRNA_position = 0

            if end_sRNA_position>len(sequence):
                end_sRNA_position = len(sequence)

            #Note that end_SRNA_position is not inclusive. So the real sequence goes up to end_SRNA_position-1
            sub_sequence = sequence[start_sRNA_position:end_sRNA_position]
            sub_sequence = sub_sequence.reverse_complement()
            sRNA = sRNA_Class(start_sRNA_position, end_sRNA_position, len(sub_sequence), sub_sequence, start_CDS, end_CDS, position, strand, gene, locus_tag)
        except:
            print("Unexpected error at get_sub_sequence:", sys.exc_info()[0])
            traceback.print_exc()
        return sRNA

    #Computes an sRNA for a CDS that is encoded backward (complement)
    def sRNA_Complement(self, sequence, start_CDS, end_CDS, strand, gene, locus_tag, position, length):
        sRNA = sRNA_Class()
        try:
            if position < 0:
                shift = - position
            else:
                shift = -(position-1)

            # We need to remove -1 because the .end position is not inclusive in python
            # That is, a sequence starts with 1 in file, but 0 in python
            # but feature.location.end gives [starts,end] where end is NOT an inclusive
            # character.

            start_gene = end_CDS - 1
            mid_position = start_gene + shift
            half_length =  int((length-1)//2)    #We substract -1 due to the mid_position
            start_sRNA_position = mid_position - half_length
            end_sRNA_position = start_sRNA_position + length

            if start_sRNA_position<0:
                start_sRNA_position = 0

            if end_sRNA_position > len(sequence):
                end_sRNA_position = len(sequence)

            # Note that end_SRNA_position is not inclusive. So the real sequence goes up to end_SRNA_position-1
            sub_sequence = sequence[start_sRNA_position:end_sRNA_position]
            sRNA = sRNA_Class(start_sRNA_position, end_sRNA_position, len(sub_sequence), sub_sequence, start_CDS, end_CDS, position, strand,
                              gene, locus_tag)
        except :
            print("Unexpected error at get_sub_sequence:", sys.exc_info()[0])
            traceback.print_exc()
        return sRNA



    #Computes the sRNAS for all CDS in the input genome
    def __get_sRNA_from_input_all_CDS(self, record_index, seq_record, position, length):

        list_sRNA = []
        for feature in seq_record.features:
            if feature.type == 'CDS':
                gene = ''
                locus_tag=''
                if 'gene' in feature.qualifiers.keys() and len(feature.qualifiers['gene'])>0:
                    gene = feature.qualifiers['gene']

                if 'locus_tag' in feature.qualifiers.keys() and len(feature.qualifiers['locus_tag'][0])>0:
                    locus_tag = feature.qualifiers['locus_tag']

                sequence = seq_record.seq
                if feature.location.strand == 1:  # Forward
                    sRNA = self.sRNA_Forward(sequence, feature.location.start, feature.location.end, feature.location.strand, gene, locus_tag, position, length)

                else:
                    if feature.location.strand == -1:  # Reverse
                        sRNA = self.sRNA_Complement(sequence, feature.location.start, feature.location.end, feature.location.strand, gene, locus_tag, position, length)

                list_sRNA.append(sRNA)
                sRNA.input_sequence = seq_record
                sRNA.input_record = record_index
        return(list_sRNA)


    # Computes the sRNAS for a set of CDS given as a list of gene_tags or locus_tags
    def __get_sRNA_from_input_listCDS(self, record_index, seq_record, position, length, gene_tags_input, locus_tags_input):

        list_sRNA = []
        for feature in seq_record.features:
            if feature.type == 'CDS':
                gene = ''
                locus_tag = ''

                if 'gene' in feature.qualifiers.keys() and len(feature.qualifiers['gene'])>0:
                    gene = feature.qualifiers['gene']

                if 'locus_tag' in feature.qualifiers.keys() and len(feature.qualifiers['locus_tag'][0]) > 0:
                    locus_tag = feature.qualifiers['locus_tag']

                compute  = False
                for g in gene:
                    if g in gene_tags_input:
                        compute = True
                        break

                if not compute:
                    for l in locus_tag:
                        if l in locus_tags_input:
                            compute = True
                            break

                if compute:

                    sequence = seq_record.seq
                    if feature.location.strand == 1:  # Forward
                        sRNA = self.sRNA_Forward(sequence, feature.location.start, feature.location.end,
                                             feature.location.strand, gene, locus_tag, position, length)

                    else:
                        if feature.location.strand == -1:  # Reverse
                            sRNA = self.sRNA_Complement(sequence, feature.location.start, feature.location.end,
                                                    feature.location.strand, gene, locus_tag, position, length)

                    sRNA.input_sequence = seq_record
                    sRNA.input_record = record_index
                    list_sRNA.append(sRNA)

        return (list_sRNA)


    #Returns the list of sRNAS
    #If a list of gene_tags or locus_tags is given the __get_sRNA_from_input_listCDS is called
    #Otherwise __get_sRNA_from_input_all_CDS gets called.
    #Note that list_sRNA is a list of lists. [i][j] The jth sRNA for the ith seqRecord
    def compute_sRNAs_from_genome(self, seq_record_list, position, length, gene_tags=None, locus_tags=None):

        list_sRNA = []
        for record_index, seq_record in enumerate(seq_record_list):
            if gene_tags or locus_tags:
                list_sRNA_perRecord = self.__get_sRNA_from_input_listCDS(record_index, seq_record, position, length, gene_tags, locus_tags)
            else:
                list_sRNA_perRecord = self.__get_sRNA_from_input_all_CDS(record_index, seq_record, position, length)

            list_sRNA.append(list_sRNA_perRecord)

        return(list_sRNA)


    #Blast each sRNA in a list of sRNAS (list_sRNA) against the input genome
    def __blast_sRNA_against_genome(self, list_sRNA, e_cutoff, identity_perc_cutoff,filepath):

        #Creates temporary files
        query_file = filepath + str(uuid.uuid4()) + '.fasta'
        subject_file = filepath + str(uuid.uuid4()) + '.fasta'


        for index, srna in enumerate(list_sRNA):
            SeqIO.write(srna.input_sequence, subject_file, "fasta")
            seq_sRNA = SeqRecord(srna.sequence_sRNA, id="sRNA")
            SeqIO.write(seq_sRNA, query_file, "fasta")
            if len(srna.sequence_sRNA)>0 and len(srna.input_sequence)>0 and len(srna.list_hits)==0:
                    list_hits = self.blastProvider.blast(query_file, subject_file, str(srna.sequence_sRNA),float(e_cutoff), float(identity_perc_cutoff))
                    srna.list_hits = list_hits

        # Remove temporary files
        if os.path.exists(query_file):
            os.remove(query_file)

        if os.path.exists(subject_file):
            os.remove(subject_file)

    #Blast all the sRNAs against the genome
    #Since list_sRNA is a list of list.
    #It calls __blast_sRNA_against_genome for each individual list
    def blast_sRNAs_against_genome(self, list_sRNA, e_cutoff, identity_perc_cutoff, filepath):
        for list_sRNA_per_record in list_sRNA:
            self.__blast_sRNA_against_genome(list_sRNA_per_record, e_cutoff, identity_perc_cutoff,filepath)
        return (list_sRNA)

    #Obtain all the sRNAs that have a hit in the genome
    #A hit is defined as an "occurrence" of the sRNA in the genome
    def get_sRNAs_with_hits(self, list_sRNA):
        list_sRNA_with_hits =[]

        for seq_record in list_sRNA:
            list = []
            for sRNA in seq_record:
                #Blast always returns the sRNA subsequence as a hit
                if len(sRNA.list_hits)>1:
                    list.append(sRNA)
            list_sRNA_with_hits.append(list)

        return list_sRNA_with_hits


    #This function re-obtains an sRNA
    def __recompute_sRNA(self, sRNA_original, position, length):
        if sRNA_original.strand == 1:  # Forward
            sRNA = self.sRNA_Forward(sRNA_original.input_sequence.seq, sRNA_original.start_position_CDS,
                                     sRNA_original.end_position_CDS, sRNA_original.strand, sRNA_original.gene, sRNA_original.locus_tag, position,
                                     length)
        else:
            if sRNA_original.strand == -1:  # Reverse
                sRNA = self.sRNA_Complement(sRNA_original.input_sequence.seq, sRNA_original.start_position_CDS,
                                            sRNA_original.end_position_CDS, sRNA_original.strand, sRNA_original.gene, sRNA_original.locus_tag,
                                            position, length)

        sRNA.input_sequence = sRNA_original.input_sequence
        sRNA.input_record = sRNA.input_record

        return (sRNA)


    #This function returns the list of recomputed sRNAs
    #list_recomputed_sRNAs is a list of list
    #list_recomputed_sRNAs[i][1] Contains the "original" sRNA
    # list_recomputed_sRNAs[i][2] Contains the re-computed sRNA that corresponds to the sRNA located in list_recomputed_sRNAs[i][1].
    #In this way odd positions correspond to original sRNAs
    #Even position correspond to re-computed sRNAs
    def recompute_sRNAs(self, list_sRNA, times, position, length):
        list_recomputed_sRNAs = []

        for seq_record in list_sRNA:
            list = []
            for sRNA in seq_record:
                list.append(sRNA)  # Original sRNA
                i = 1
                while i <= times:
                    i = i + 1
                    sRNA_rec = self.__recompute_sRNA(sRNA, position * 1, length)
                    list.append(sRNA_rec)
            list_recomputed_sRNAs.append(list)

        return list_recomputed_sRNAs


    #Obtain the list of sRNAs that have a hit in the genome
    #Recomputes the sRNAs that have hits in the genome
    #Blast the recomputed sRNAS against the input genome
    def follow_sRNAS_with_hits(self, list_sRNA, shift_hits, length, e_cutoff, identity_perc, filepath_temp):
        list_sRNA_with_hits = self.get_sRNAs_with_hits(list_sRNA)

        # 3.2 Recompute sRNAS with hits
        list_sRNA_recomputed = self.recompute_sRNAs(list_sRNA_with_hits, 1, int(shift_hits), int(length))

        # 3.3 Blast re-computed sRNAs
        try:
            self.blast_sRNAs_against_genome(list_sRNA_recomputed, e_cutoff, identity_perc, filepath_temp)
        except Exception as e:
            print('An exception occurred at blasting sRNAS (recomputed)')
            list_sRNA_recomputed = []

        return list_sRNA_recomputed

    #Obtain the list of sRNAS by calling the corresponding functions either
    #for all the CDS or for a specific list
    def get_sRNAs(self, sequence_record_list, shift, length, only_tags, gene_tags, locus_tags):
        if only_tags:
            # 2.1. For a specific set of locus gene tags
            if len(gene_tags) == 0 and len(locus_tags) == 0:
                print('(%s) - Error at reading gene/locus tags - End of Task' % self.request.id)
                raise KeyError()
            else:
                list_sRNA = self.compute_sRNAs_from_genome(sequence_record_list, int(shift), int(length), gene_tags,
                                                           locus_tags)
        else:
            # 2.2. For all CDS
            list_sRNA = self.compute_sRNAs_from_genome(sequence_record_list, int(shift), int(length))

        return list_sRNA

    #Maps a sRNA.hit to a dict (for exporting purposes)
    def sRNA_hit_to_dict(self, srna, record, hit=None):
        dict={}
        dict["Record"] = str(record)
        dict["sRNA"] = str(srna.sequence_sRNA)
        dict["Strand"] = srna.strand
        dict["Gene"] = srna.gene
        dict["Locus Tag"] = srna.locus_tag
        dict["sRNA Start"] = self._start_in_file(srna.start_position_sRNA)
        dict["sRNA End"] = self._end_in_file(srna.end_position_sRNA)
        dict["sRNA Length"]= srna.length_sRNA
        dict["Shift/Position"] = srna.shift
        dict["CDS Start"]= self._start_in_file(srna.start_position_CDS)
        dict["CDS End"]= self._end_in_file(srna.end_position_CDS)
        if hit:
            dict["Hit Start"]= int(hit.sbjct_start)
            dict["Hit End"]= hit.sbjct_end
            dict["Expected Value"]= hit.expect
            dict["Align Length"]= hit.align_length
            dict["Perc. Identity"]= (hit.score/srna.length_sRNA)*100
            dict["sRNA Itself"] = ""
            if srna.strand==-1 and srna.start_position_sRNA+1==int(hit.sbjct_start):
                dict["sRNA Itself"] = "*"
            if srna.strand==1 and srna.start_position_sRNA+1==int(hit.sbjct_end):
                dict["sRNA Itself"] = "*"
        else:
            dict["Hit Start"] = ''
            dict["Hit End"] = ''
            dict["Expected Value"] = ''
            dict["Align Length"] = ''
            dict["Perc. Identity"] = ''

        return dict


    #Creates a list of data frames where each data frame corresponds to an sRNA from a list of sRNAs given as a input
    def sRNAs_to_data_frames(self, list_sRNA, seq_file, format, position, length, e_cutoff, perc_identity):

        name = seq_file

        # Creates panda data frame with general info
        general_info = {
            "User Parameters": '',
            "Input File": seq_file,
            "Format": format,
            "Position": position,
            "Length": length,
            "Expected cutoff": e_cutoff,
            "Percentage Indentity": perc_identity
        }

        df_ginfo = pd.DataFrame.from_dict(general_info, orient='index')
        df_ginfo.rename(columns={0: ' '}, inplace=True)

        # Creates panda date frame with column headings
        headings = {
            "Record": '',
            "sRNA": '',
            "Strand": '',
            "Gene": '',
            "Locus Tag": '',
            "sRNA Start": '',
            "sRNA End": '',
            "sRNA Length": '',
            "Shift/Position": '',
            "CDS Start": '',
            "CDS End": '',
            "Hit Start": '',
            "Hit End": '',
            "Expected Value": '',
            "Align Length": '',
            "Perc. Identity": '',
            "sRNA Itself": '',
        }

        df_headings = pd.DataFrame([headings])

        # Creates panda data frame with sRNA information
        list_rows = []
        row = 10
        index_record = 1
        for record in list_sRNA:
            for srna in record:
                if len(srna.list_hits) == 0:
                    dict = self.sRNA_hit_to_dict(srna, index_record)
                    list_rows.append(dict)

                for hit in srna.list_hits:
                    dict = self.sRNA_hit_to_dict(srna, index_record, hit)
                    list_rows.append(dict)
            index_record = index_record + 1

        df_rows = pd.DataFrame(list_rows)

        return df_ginfo, df_headings, df_rows


    def tags_to_data_frame(self, list_sRNA):
        gene_tags = []
        locus_tags = []

        for record in list_sRNA:
            for sRNA in record:
                for gene in sRNA.gene:
                    if gene not in gene_tags:
                        gene_tags.append(gene)

                for locus in sRNA.locus_tag:
                    if locus not in locus_tags:
                        locus_tags.append(locus)

        if len(gene_tags) != len(locus_tags):
            if len(gene_tags) > len(locus_tags):
                i = len(locus_tags)
                while (i < len(gene_tags)):
                    locus_tags.append('')
                    i = i + 1

            if len(locus_tags) > len(gene_tags):
                i = len(gene_tags)
                while (i < len(locus_tags)):
                    gene_tags.append('')
                    i = i + 1

        dict = {'Gene_Tag': gene_tags, 'Locus_Tag': locus_tags}
        df = pd.DataFrame(dict)
        return df



    def export_output_return_bytes(self, seq_file, format, position, length, e_cutoff, perc_identity, list_sRNA_recomputed=None, list_sRNA=None):

        # Writes frames to excel
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')

        #Export only sRNAS with hits
        if list_sRNA_recomputed:
            df_ginfo, df_headings, df_rows = self.sRNAs_to_data_frames(list_sRNA_recomputed, seq_file, format, position, length, e_cutoff, perc_identity)
            df_ginfo.to_excel(writer, sheet_name="Hits", index=True)
            df_headings.to_excel(writer, startrow=9, sheet_name="Hits", index=False)
            df_rows.to_excel(writer, sheet_name="Hits", startrow=10, index=False, header=False)

        #Export all sRNAS
        if list_sRNA:
            df_ginfo, df_headings, df_rows = self.sRNAs_to_data_frames(list_sRNA, seq_file, format, position,length, e_cutoff, perc_identity)
            df_ginfo.to_excel(writer, sheet_name="All", index=True)
            df_headings.to_excel(writer, startrow=9, sheet_name="All", index=False)
            df_rows.to_excel(writer, sheet_name="All", startrow=10, index=False, header=False)

        #Export gene tags and locs tags of sRNAS with hits
        if list_sRNA_recomputed:
            df = self.tags_to_data_frame(list_sRNA_recomputed)
            df.to_excel(writer, sheet_name="Tags", header=True, index=False)

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()
        output.seek(0)
        return output



    def export_output(self, seq_file, format, position, length, e_cutoff, perc_identity, filename, list_sRNA_recomputed=None,
                      list_sRNA=None):

        # Writes frames to excel
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')

        # Export only sRNAS with hits
        if list_sRNA_recomputed:
            df_ginfo, df_headings, df_rows = self.sRNAs_to_data_frames(list_sRNA_recomputed, seq_file, format, position,
                                                                       length, e_cutoff, perc_identity)
            df_ginfo.to_excel(writer, sheet_name="Hits", index=True)
            df_headings.to_excel(writer, startrow=9, sheet_name="Hits", index=False)
            df_rows.to_excel(writer, sheet_name="Hits", startrow=10, index=False, header=False)

        # Export all sRNAS
        if list_sRNA:
            df_ginfo, df_headings, df_rows = self.sRNAs_to_data_frames(list_sRNA, seq_file, format, position, length,
                                                                       e_cutoff, perc_identity)
            df_ginfo.to_excel(writer, sheet_name="All", index=True)
            df_headings.to_excel(writer, startrow=9, sheet_name="All", index=False)
            df_rows.to_excel(writer, sheet_name="All", startrow=10, index=False, header=False)

        # Export gene tags and locs tags of sRNAS with hits
        if list_sRNA_recomputed:
            df = self.tags_to_data_frame(list_sRNA_recomputed)
            df.to_excel(writer, sheet_name="Tags", header=True, index=False)

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()








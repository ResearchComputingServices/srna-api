# Import here the corresponding headers
from flask import Response
from flask import json
from flask import request, send_file
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.decorators.authentication import authentication
from srna_api.providers.sRNA_provider import sRNA_Provider


sRNA_provider = sRNA_Provider()


def _read_input_sequence(sequence_to_read,accession_number,format):

    sequence_record_list=[]

    #1.1 Read an attached sequence file
    if sequence_to_read:
        # Read file_sequence
        print('Read sequence')
        sequence_record_list = sRNA_provider.read_input_sequence(sequence_to_read, format)
    else:
        # 1.2 Fetch the sequence in Entrez database using accession number
        if accession_number:
            # Fetch the sequence using accession number
            print("Fetch sequence from Entrez using Accession Number")
            sequence_record_list = sRNA_provider.fetch_input_sequence(accession_number)

    return sequence_record_list



def _compute_srnas(sequence_to_read, accession_number, format, shift, length, only_tags, file_tags, e_cutoff,identity_perc, follow_hits, shift_hits):

    #1. Obtain input sequence
    sequence_record_list =  _read_input_sequence(sequence_to_read,accession_number,format)

    if len(sequence_record_list)==0:
        #Error occurred at reading the sequence
        error = {"message": "An error occurred when retrieving sequence"}
        response = Response(json.dumps(error), 400, mimetype="application/json")
        return response


    sequence_name = sequence_record_list[0].name

    #2. Compute sRNA
    if only_tags:
        # 2.1. For a specific set of locus gene tags
        print('Compute sRNAs for a specific set of locus or gene tags')
        gene_tags, locus_tags = sRNA_provider.load_locus_gene_tags(file_tags)

        if len(gene_tags)==0 and len(locus_tags)==0:
            error = {"message": "An error occurred when retrieving gene/locus tags"}
            response = Response(json.dumps(error), 400, mimetype="application/json")
            return response
        else:
            print('Compute sRNAS for a list of gene/locus tags')
            list_sRNA = sRNA_provider.compute_sRNAs_from_genome(sequence_record_list, int(shift), int(length), gene_tags,locus_tags)
    else:
        # 2.2. For all CDS
        print ('Compute sRNAs for all CDS in genome')
        list_sRNA = sRNA_provider.compute_sRNAs_from_genome(sequence_record_list, int(shift), int(length))


    #3. Blast each sRNA against input genome
    print('Blast each sRNA against input genome \n')
    try:
        sRNA_provider.blast_sRNAs_against_genome(list_sRNA, e_cutoff, identity_perc)
    except Exception as e:
        print('An exception occurred at blasting re-computed sRNAS')
        follow_hits=False

    #4 (optional)
    #Recompute sRNAS for all sRNAS that have hits other than themselves in the genome
    list_sRNA_recomputed = []

    if follow_hits:
        #4.1 Obtan sRNAs with hits
        print('Get sRNA with hits \n')
        list_sRNA_with_hits = sRNA_provider.get_sRNAs_with_hits(list_sRNA)

        #4.2 Recompute sRNAS with hits
        print('Recompute sRNAs for sRNAs with hits')
        list_sRNA_recomputed = sRNA_provider.recompute_sRNAs(list_sRNA_with_hits, 1, int(shift_hits),int(length))

        #4.3 Blast re-computed sRNAs
        print('Blast the re-computed sRNAs')
        try:
            sRNA_provider.blast_sRNAs_against_genome(list_sRNA_recomputed, e_cutoff, identity_perc)
        except Exception as e:
            print ('An exception occurred at blasting re-computed sRNAS')
            list_sRNA_recomputed = []

    #5 Return output
    output = sRNA_provider.export_output(sequence_name, format, shift, length, e_cutoff, identity_perc, list_sRNA_recomputed, list_sRNA)

    return send_file(output, attachment_filename="sRNA Result" + '.xlsx',mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, cache_timeout=-1)


def _validate_request(sequence_to_read, accession_number, format, shift, length, only_tags, file_tags, e_cutoff, identity_perc, follow_hits, shift_hits):
    error = ''
    # Returns error if neither a file sequence or an accession number was provided
    if not sequence_to_read and not accession_number:
        error = {"message": "A sequence file or an accession number must be provided."}
        return error

    if sequence_to_read and not format:
        error = {"message": "A format must be provided for the sequence file"}
        return error

    if not isinstance(shift, int):
        error = {"message": "Shift value must be an integer."}
        return error
    else:
        if shift == 0:
            error = {"message": "Shift value cannot be zero."}
            return error

    if not isinstance(length, int):
        error = {"message": "Length value must be an integer."}
        return error
    else:
        if length <= 0:
            error = {"message": "The  length must be greater than zero."}
            return error

    if only_tags and not file_tags:
        error = {"A file with locus or gene tags should be provided."}
        return error

    if not isinstance(e_cutoff, float):
        error = {"message": "Invalid expected cutoff"}
        return error

    if not isinstance(identity_perc, float):
        error = {"message": "Invalid percentage of identity"}
        return error
    else:
        if identity_perc < 0 or identity_perc > 1:
            error = {"message": "Percentage of identity must be between 0 and 1."}
            return error

    if follow_hits:
        if not isinstance(shift_hits, int):
            error = {"message": "Shift (for recomputing) value must be an integer."}
            return error
        else:
            if shift_hits == 0:
                error = {"message": "Shift (for recomputing) value cannot be zero."}
                return error

    return error



@srna_bp.route("/compute_srnas", methods=['POST'])
@crossdomain(origin='*')
@authentication
def compute_srnas():
    try:
        #Read file sequence into a text string
        sequence_to_read = request.files['file_sequence'].read().decode('utf-8')
        data = request.form
        format = data.get('format')
        shift = int(data.get('shift')) if data.get('shift') else None
        length = int(data.get('length')) if data.get('length') else None

        if (data.get('only_tags') and data.get('only_tags') == 'True'):
            only_tags = True
        else:
            only_tags = False

        e_cutoff = float(data.get('e_cutoff')) if data.get('e_cutoff') else None
        identity_perc = float(data.get('identity_perc')) if data.get('identity_perc') else None

        if (data.get('follow_hits') and data.get('follow_hits') == 'True'):
            follow_hits = True
        else:
            follow_hits = False


        shift_hits = data.get('shift_hits')
        if len(shift_hits)>0:
            shift_hits = int(shift_hits)
        else:
            shift_hits = None

        accession_number = data.get('accession_number')

        if only_tags==True:
            file_tags = request.files['file_tags']
        else:
            file_tags = None

        error = _validate_request(sequence_to_read, accession_number, format, shift, length, only_tags, file_tags, e_cutoff, identity_perc, follow_hits, shift_hits)
        if len(error) > 0:
            response = Response(json.dumps(error), 400, mimetype="application/json")
            return response



        response = _compute_srnas(sequence_to_read, accession_number, format, shift, length, only_tags, file_tags, e_cutoff,
                       identity_perc, follow_hits, shift_hits)

        if not response:
            error = {"message": "An error occurred when processing the request"}
            response = Response(json.dumps(error), 400, mimetype="application/json")
            return response

    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
    return response

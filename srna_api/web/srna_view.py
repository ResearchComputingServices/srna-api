# Import here the corresponding headers
from flask import Response
from flask import json
from flask import request, send_file
from srna_api.web.common_view import srna_bp
from srna_api.decorators.crossorigin import crossdomain
from srna_api.providers.sRNA_provider import sRNA_Provider
from srna_api.extensions import celery
from flask import jsonify
import io
import os
import uuid
from werkzeug import secure_filename
import sys
import traceback
import time
import random

sRNA_provider = sRNA_Provider()

def remove_file(filename):
    if os.path.exists(filename):
        os.remove(filename)



def upload_file(file, name):
    if file and name:
        folder = 'srna-data/input_files'
        filename = secure_filename(name)
        if not os.path.exists(folder):
            os.makedirs(folder)
        fullpath = os.path.join(folder, filename)
        file.save(fullpath)
        return fullpath


def download_file(filename):
    filename = filename + '.xlsx'
    fullpath = "srna-data/output_files/" + filename
    if os.path.exists(fullpath):
        with open(fullpath, 'rb') as binary:
            return send_file(
                io.BytesIO(binary.read()),
                attachment_filename=filename,
                as_attachment=True,
                mimetype="application/binary")

    error = {"message": "File does not exist"}
    return Response(json.dumps(error), 404, mimetype="application/json")



@celery.task(bind=True)
def _compute_srnas(self, sequence_to_read, accession_number, format, shift, length, only_tags, blast, e_cutoff,identity_perc, follow_hits, shift_hits, gene_tags, locus_tags):

    try:
        print('(%s) - 1: Task Started' %self.request.id)

        #Path for temporary location
        filepath_temp = "srna-data/temp_files/"
        # 1. Obtain input sequence
        print('(%s) - 2: Reading sequence' % self.request.id)
        sequence_record_list = sRNA_provider.load_input_sequence(sequence_to_read, accession_number, format)

        if len(sequence_record_list) == 0:
            # Error occurred at reading the sequence
            print('(%s) - Error at reading sequence file - End of Task' % self.request.id)
            raise KeyError()

        #2. Compute sRNA
        print('(%s) - 3: Compute sRNAS' % self.request.id)
        list_sRNA = sRNA_provider.get_sRNAs(sequence_record_list, shift, length, only_tags, gene_tags, locus_tags)

        #3. Blast each sRNA against input genome
        if blast:
            print('(%s) - 4: Blast each sRNA against input genome' % self.request.id)
            start = time.time()
            try:
                sRNA_provider.blast_sRNAs_against_genome(list_sRNA, e_cutoff, identity_perc, filepath_temp)
            except Exception as e:
                print('(%s) - An exception occurred at blasting sRNAS'  % self.request.id)
                follow_hits=False

            end = time.time()
            print('(%s) - 5: End of blasting. Total mins: %f' % (self.request.id,(end - start) / 60))
        else:
            follow_hits = False

        #5 (optional)
        #Recompute sRNAS for all sRNAS that have hits other than themselves in the genome
        list_sRNA_recomputed = []

        if follow_hits:
            print('(%s) - 6: Following Hits' % self.request.id)
            list_sRNA_recomputed = sRNA_provider.follow_sRNAS_with_hits(list_sRNA,shift_hits,length,e_cutoff,identity_perc,filepath_temp)

        #6 Export output
        print('(%s) - 7: Exporting Output' % self.request.id)
        output_file_name = str(self.request.id)
        filepath_output = "srna-data/output_files/" + output_file_name + ".xlsx"
        sequence_name = sequence_record_list[0].name
        sRNA_provider.export_output(sequence_name, format, shift, length, e_cutoff, identity_perc, filepath_output, list_sRNA_recomputed, list_sRNA)

        #7. Remove temporal input sequence
        print('(%s) - 8: Deleting temporal input' % self.request.id)
        os.remove(sequence_to_read)

    except Exception as e:
            # Remove temporal input sequence
            print('(%s) - Deleting temporal input' % self.request.id)
            os.remove(sequence_to_read)
            print("Unexpected error at _compute_srnas:", sys.exc_info()[0])
            print('(%s) - Exception occurred' % self.request.id)
            traceback.print_exc()
            #Throwing this exception on purpose to set the celery task as FAILURE
            #This would be equivalent as removing the try/except
            #Otherwise the task.state is always SUCCESS
            raise KeyError()
            return 'Error'

    print('(%s) - 9: Task Completed' % self.request.id)
    return ('Done')




def _validate_request(sequence_to_read, accession_number, format, shift, length, only_tags, file_tags, blast, e_cutoff, identity_perc, follow_hits, shift_hits):
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

    if blast:
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
                else:
                    if shift_hits==shift:
                        error = {"message": "Shift and Shift (for recomputing) must be different."}
                        return error

    return error




@srna_bp.route("/compute_srnas", methods=['POST'])
@crossdomain(origin='*')
def compute_srnas():
    try:
        #Obtain request parameters
        file = request.files.get('file_sequence')
        name = str(uuid.uuid4()) + '_' + file.filename
        data = request.form
        format = data.get('format')
        shift = int(data.get('shift')) if data.get('shift') else None
        length = int(data.get('length')) if data.get('length') else None
        e_cutoff = float(data.get('e_cutoff')) if data.get('e_cutoff') else None
        identity_perc = float(data.get('identity_perc')) if data.get('identity_perc') else None
        shift_hits = int(data.get('shift_hits')) if data.get('shift_hits') else None
        accession_number = data.get('accession_number')

        if (data.get('only_tags') and data.get('only_tags') == 'true'):
            only_tags = True
        else:
            only_tags = False

        if (data.get('follow_hits') and data.get('follow_hits') == 'true'):
            follow_hits = True
        else:
            follow_hits = False

        if only_tags==True:
            file_tags = request.files['file_tags']
        else:
            file_tags = None

        if (data.get('blast') and data.get('blast') == 'true'):
            blast = True
        else:
            blast = False

        #1. Upload input file
        if file:
            sequence_to_read = upload_file(file, name)
        else:
            error = {"message": "Please provided an input file to process. Check request format."}
            response = Response(json.dumps(error), 400, mimetype="application/json")
            return response

        #2. Validate request parameters
        error = _validate_request(sequence_to_read, accession_number, format, shift, length, only_tags, file_tags, blast, e_cutoff, identity_perc, follow_hits, shift_hits)
        if len(error) > 0:
            response = Response(json.dumps(error), 400, mimetype="application/json")
            remove_file(sequence_to_read)
            return response

        #3. Validate if input sequence and format are a valid biopython input
        sequence_record_list = sRNA_provider.load_input_sequence(sequence_to_read, accession_number, format)

        if len(sequence_record_list) == 0:
            # Error occurred at reading the sequence
             error = {"message": "An error occurred when reading sequence. Please verify file and that format corresponds to the sequence file."}
             response = Response(json.dumps(error), 400, mimetype="application/json")
             remove_file(sequence_to_read)
             return response

        #4. Obtain gene tags and locus tags
        gene_tags=[]
        locus_tags=[]
        if only_tags:
            gene_tags, locus_tags = sRNA_provider.load_locus_gene_tags(file_tags)

            if len(gene_tags) == 0 and len(locus_tags) == 0:
                error = {"message": "An error occurred when retrieving gene/locus tags. Please verify the format of the tags file."}
                response = Response(json.dumps(error), 400, mimetype="application/json")
                remove_file(sequence_to_read)
                return response

        #5. Call sRNA computation
        task = _compute_srnas.delay(sequence_to_read, accession_number, format, shift, length, only_tags, blast, e_cutoff, identity_perc, follow_hits, shift_hits, gene_tags, locus_tags)

        if not task:
            error = {"message": "An error occurred when processing the request"}
            response = Response(json.dumps(error), 400, mimetype="application/json")
            remove_file(sequence_to_read)
            return response
        else:
            return jsonify({'Task_id': task.id, 'Task_status': task.status}), 202, {}

    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
        remove_file(sequence_to_read)
        return response



@srna_bp.route("/get_output_file", methods=['GET'])
@crossdomain(origin='*')
def get_output_file():
    try:
        task_id = request.args.get('task_id')

        if not task_id:
            error = {"message": "Expected File Id. Check the format of the request."}
            response = Response(json.dumps(error), 400, mimetype="application/json")
            return response

        return download_file(task_id)

    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
        return response


@srna_bp.route("/get_task_status", methods=['GET'])
@crossdomain(origin='*')
def get_task_status():
    try:

        task_id = request.args.get('task_id')

        if not task_id:
            error = {"message": "Expected Task Id. Check the format of the request."}
            response = Response(json.dumps(error), 400, mimetype="application/json")
            return response

        res = celery.AsyncResult(task_id)
        print(res.status)

        return jsonify({'Task_id': task_id, 'Task_status': res.status}), 200, {}

    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
        return response


@srna_bp.route("/get_tasks_status", methods=['POST'])
@crossdomain(origin='*')
def get_tasks_status():
    try:

        data = request.get_json()
        if not data:
            error = {"message": "Expected Lists of Tasks. Check format of the request."}
            response = Response(json.dumps(error), 400, mimetype="application/json")
            return response

        tasks = data.get('tasks')
        status = []
        for task_id in tasks:
            res = celery.AsyncResult(task_id)
            dict = {'Task_id': task_id, 'Task_status': res.status}
            status.append(dict)

        return jsonify(status), 200, {}

    except Exception as e:
        error = {"exception": str(e), "message": "Exception has occurred. Check the format of the request."}
        response = Response(json.dumps(error), 500, mimetype="application/json")
        return response

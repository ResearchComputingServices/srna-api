from srna_api.providers import sRNA_Provider
from srna_api.providers import fileSystem_Provider
from srna_api.extensions import oidc
from srna_api.web import srna_view
import sys, getopt
from srna_api.extensions import celery
import redis

sRNA_provider = sRNA_Provider()
file_provider = fileSystem_Provider()

input_folder =  oidc.client_secrets["input_folder"]
output_folder =  oidc.client_secrets["output_folder"]
temp_folder =  oidc.client_secrets["temp_folder"]

def get_celery_queue_in_redis():
    r = redis.Redis("localhost", 6379)
    celery_jobs = r.llen('celery')
    print ('Tasks in queue: {}'.format(celery_jobs))
    return celery_jobs

def get_total_tasks_in_celery():
    # Inspect all nodes.
    insp = celery.control.inspect()
    #Active tasks (being processed by a worker)
    active_lst = insp.active()
    #Tasks scheduled to be processed
    scheduled_lst = insp.scheduled()
    #Tasks received by a worker but not yet scheduled
    reserved_lst = insp.reserved()

    total_tasks = 0
    t = 0
    if active_lst:
        for key in active_lst:
            total_tasks = total_tasks + len(active_lst[key])
            t = t + len(active_lst[key])
        print('Active tasks: {}'.format(t))

    t=0
    if scheduled_lst:
        for key in scheduled_lst:
            total_tasks = total_tasks + len(scheduled_lst[key])
            t = t + len(scheduled_lst[key])
        print('Scheduled tasks: {}'.format(t))

    t=0
    if reserved_lst:
        for key in reserved_lst:
            total_tasks = total_tasks + len(reserved_lst[key])
            t = t + len(reserved_lst[key])
        print('Reserved tasks: {}'.format(t))

    print('Total tasks at Celery: {}'.format(total_tasks))
    return total_tasks



def make_requests():
    try:
        #1 Obtain request parameters
        client_session = "test_session"
        sequence_to_read = "srna-data/temp_files/test.gbk"
        format = 'genbank'
        shift = -8
        length = 21
        e_cutoff = 0.01
        identity_perc = 0.8
        shift_hits = 10
        accession_number = ""
        only_tags = False
        follow_hits = True
        file_tags = None
        blast = True

        #Validate if input sequence and format are a valid biopython input
        sequence_record_list = sRNA_provider.load_input_sequence(sequence_to_read, accession_number, format)

        if len(sequence_record_list) == 0:
            # Error occurred at reading the sequence
             return "Error"


        gene_tags=[]
        locus_tags=[]

        #Create ouput folder per session id
        file_provider.create_folder(output_folder, client_session)

        #Call sRNA computation
        task = srna_view._compute_srnas.delay(sequence_to_read, accession_number, format, shift, length, only_tags, blast, e_cutoff, identity_perc, follow_hits, shift_hits, gene_tags, locus_tags, client_session)

        if not task:
            return "Error"
        else:
            return task.id

    except Exception as e:
        return "Error"


def test_load(number_requests):
    i=0
    error = 0
    while (i<number_requests):
        result = make_requests()
        if result=='Error':
            print ('Request {} - Error'.format(i+1))
            error = error + 1
        else:
            print('Request {} - Success'.format(i + 1))
        i=i+1
    return error




if __name__ == '__main__':


    number = 5
    if len(sys.argv) > 1:
        argv = sys.argv[1:]

        try:
            opts, args = getopt.getopt(argv, "n:")
            for opt, arg in opts:
                if opt in ("-n", "--number"):
                    num_str = arg
            number = int(num_str)
        except getopt.GetoptError:
            number = 5

    print ('Making {} requests'.format(number))
    errors = test_load(number)
    print('Faulty {} requests '.format(errors))

    get_total_tasks_in_celery()
    get_celery_queue_in_redis()



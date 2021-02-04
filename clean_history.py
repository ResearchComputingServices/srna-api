from srna_api.providers.fileSystem_provider import fileSystem_Provider
from srna_api.extensions import oidc

file_provider = fileSystem_Provider()

input_folder =  oidc.client_secrets["input_folder"]
output_folder =  oidc.client_secrets["output_folder"]
temp_folder =  oidc.client_secrets["temp_folder"]

input_days=  oidc.client_secrets["clean_input_folder_days"]
output_days =  oidc.client_secrets["clean_output_folder_days"]
temp_days =  oidc.client_secrets["clean_temp_folder_days"]


if __name__ == '__main__':
    print ('Removing files from ')
    print (output_folder)
    file_provider.clean_history(output_folder, False, output_days)
    print('Removing files from ')
    print(input_folder)
    file_provider.clean_history(input_folder, False, input_days)
    print('Removing files from ')
    print(temp_folder)
    file_provider.clean_history(temp_folder, False, temp_days)

    file_provider.create_folder_fullpath(input_folder)
    file_provider.create_folder_fullpath(output_folder)
    file_provider.create_folder_fullpath(temp_folder)

    print('Done!')
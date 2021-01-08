if __name__ == '__main__':
    import os
    python_version = os.popen('python3 --version').read().split(' ')[1]
    python_folder = 'python{}'.format(python_version[0: 3])
    certifi_folder = 'env/lib/{}/site-packages/certifi'.format(python_folder)

    if not os.path.exists('ssl'):
        print('Fetching ssl...')
        os.system('git clone https://rcs-git.carleton.ca/development/ssl')
    
    print('Creating certificate...')
    os.system('cat {certifi_folder}/cacert.pem ssl/permafrost_carleton_ca.pem > {certifi_folder}/new_cacert.pem'.format(certifi_folder=certifi_folder))
    os.system('mv {certifi_folder}/cacert.pem {certifi_folder}/old_cacert.pem'.format(certifi_folder=certifi_folder))
    os.system('mv {certifi_folder}/new_cacert.pem {certifi_folder}/cacert.pem'.format(certifi_folder=certifi_folder))
    print('DONE')

# Import here the corresponding headers
from flask import Response
from flask import json
from flask import send_file
import io
import os
import shutil
from werkzeug import secure_filename


class fileSystem_Provider:

    def create_folder(self, path, folder):
        fullpath = os.path.join(path, folder)
        if not os.path.exists(fullpath):
            os.makedirs(fullpath)

    def remove_file(self,filename):
        if os.path.exists(filename):
            os.remove(filename)


    def upload_file(self, folder, file, name):
        if file and name:
            #path = 'srna-data/input_files'
            filename = secure_filename(name)
            if not os.path.exists(folder):
                os.makedirs(folder)
            fullpath = os.path.join(folder, filename)
            file.save(fullpath)
            return fullpath

    def download_file(self, folder , filename):
        filename = filename + '.xlsx'
        #fullpath = "srna-data/output_files/" + filename
        fullpath = folder + filename
        if os.path.exists(fullpath):
            with open(fullpath, 'rb') as binary:
                return send_file(
                    io.BytesIO(binary.read()),
                    attachment_filename=filename,
                    as_attachment=True,
                    mimetype="application/binary")

        error = {"message": "File does not exist"}
        return Response(json.dumps(error), 404, mimetype="application/json")


    def remove_files_with_prefix(self, path, prefix):
        for file in os.listdir(path):
            if file.startswith(prefix):
                print(file)
                filename = path + file
                self.remove_file(filename)
        print ('done')
        return

    def remove_files_in_folder(self, folder):
        for file in os.listdir(folder):
            filename = folder + file
            self.remove_file(filename)
        return

    def remove_folder(self, folder):
        if os.path.exists(folder):
            os.rmdir(folder)



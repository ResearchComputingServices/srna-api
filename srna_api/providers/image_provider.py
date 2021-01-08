from srna_api.providers.base_provider import BaseProvider
import io
from flask import json, Response, send_file

class ImageProvider(BaseProvider):
    def download_file(self, fullpath, filename):
        with open(fullpath, 'rb') as binary:
            return send_file(
                io.BytesIO(binary.read()),
                attachment_filename=filename,
                as_attachment=True,
                mimetype="application/binary")
        return Response(json.dumps([]), 404, mimetype="application/json", cache_timeout=-1)
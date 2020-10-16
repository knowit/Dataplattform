from dataplattform.common.handlers.ingest import IngestHandler
from dataplattform.common.schema import Data, Metadata
from dataplattform.common import raw_storage as rs
import numpy
from PIL import Image
import io
from datetime import datetime


handler = IngestHandler()


@handler.ingest()
def ingest(event) -> Data:
    timestamp_now = datetime.now().timestamp()
    d = [{'test': 'This is a test message', 'id': 1, 'time_presice': str(datetime.now().timestamp())},
         {'test': 'This is also a test message', 'id': 2, 'time_presice': str(datetime.now().timestamp())}]

    d2 = Data(
        metadata=Metadata(timestamp=int(timestamp_now)),
        data=d)

    # create an image here first
    imarray = numpy.random.rand(100, 100, 3) * 255
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
    img_byte_arr = io.BytesIO()
    im.save(img_byte_arr, format='PNG')
    rs.write_to_public_bucket(img_byte_arr.getvalue(), ext='png')

    img_byte_arr2 = io.BytesIO()
    imarray2 = numpy.random.rand(100, 100, 3) * 255
    im2 = Image.fromarray(imarray2.astype('uint8'))
    im2.save(img_byte_arr2, format='pdf')
    rs.write_to_private_bucket(img_byte_arr2.getvalue(), ext='pdf')

    return d2


import unittest
import io
import os

import PIL.Image
import iso19794

#_______________________________________________________________________________
class TestFIR(unittest.TestCase):
    
    def test_fir1(self):
        # check we can read an ISO image
        i = PIL.Image.open(os.path.join(os.path.dirname(__file__),'annexc.fir'))
        self.assertEqual(i.info['nb_representation'],1)
        self.assertEqual(i.info['nb_position'],1)
        # self.assertEqual(i.info['length'],234441)
        i.header['position'] = 'RIGHT_RING_FINGER'
        self.assertRaises(EOFError,i.seek,1)
        # rotate the image
        i2 = i.rotate(45,expand=True,fillcolor=128)        
        i2.header = i.header
        i2.header = i.header
        # check we can save it
        buf = io.BytesIO()
        i2.save(buf,"FIR")
        self.assertGreater( len(buf.getvalue()) , 1000 )

    def test_fir2(self):
        # check we can read an ISO image
        i = PIL.Image.open(os.path.join(os.path.dirname(__file__),'twofingers.fir'))
        self.assertEqual(i.info['nb_representation'],2)
        self.assertEqual(i.info['nb_position'],2)
        self.assertEqual(i.header['position'],'LEFT_INDEX_FINGER')
        i.rotate(90)
        i.seek(1)
        i.rotate(90)
        self.assertEqual(i.info['nb_representation'],2)
        self.assertEqual(i.info['nb_position'],2)
        self.assertEqual(i.header['position'],'LEFT_MIDDLE_FINGER')
        self.assertRaises(EOFError,i.seek,2)

    def test_multi(self):
        i1 = PIL.Image.open(os.path.join(os.path.dirname(__file__),'annexc.fir'))
        i2 = PIL.Image.open(os.path.join(os.path.dirname(__file__),'twofingers.fir'))
        buf = io.BytesIO()
        i1.save(buf,"FIR",save_all=True,append_images=[i2])

        i = PIL.Image.open(buf)
        self.assertEqual(i.info['nb_representation'],3)
        self.assertEqual(i.info['nb_position'],2)

# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main()
    

	

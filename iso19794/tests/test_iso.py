
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
        self.assertEqual(i.header.nb_repr,1)
        self.assertEqual(i.header.nb_pos,1)
        self.assertEqual(i.header.length,234441)
        i.rheader = i.rheader._replace(position = 'Right ring finger')
        self.assertRaises(EOFError,i.seek,1)
        # rotate the image
        i2 = i.rotate(45,expand=True,fillcolor=128)        
        i2.header = i.header
        i2.rheader = i.rheader
        # check we can save it
        buf = io.BytesIO()
        i2.save(buf,"FIR")
        self.assertGreater( len(buf.getvalue()) , 1000 )

    def test_fir2(self):
        # check we can read an ISO image
        i = PIL.Image.open(os.path.join(os.path.dirname(__file__),'twofingers.fir'))
        self.assertEqual(i.header.nb_repr,2)
        self.assertEqual(i.header.nb_pos,2)
        self.assertEqual(i.rheader.position,'Left index finger')
        i.rotate(90)
        i.seek(1)
        i.rotate(90)
        self.assertEqual(i.header.nb_repr,2)
        self.assertEqual(i.header.nb_pos,2)
        self.assertEqual(i.rheader.position,'Left middle finger')
        self.assertRaises(EOFError,i.seek,2)

    def test_multi(self):
        i1 = PIL.Image.open(os.path.join(os.path.dirname(__file__),'annexc.fir'))
        i2 = PIL.Image.open(os.path.join(os.path.dirname(__file__),'twofingers.fir'))
        buf = io.BytesIO()
        i1.save(buf,"FIR",save_all=True,append_images=[i2])

        i = PIL.Image.open(buf)
        self.assertEqual(i.header.nb_repr,3)
        self.assertEqual(i.header.nb_pos,2)

# ______________________________________________________________________________
if __name__=='__main__':
    unittest.main()
    

	

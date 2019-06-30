
# Implementation of Annex C1 to give a sample image

if __name__=='__main__':
    with open('annexc.fir','wb') as f:
        f.write(b'\x46\x49\x52\x00')
        f.write(b'\x30\x32\x30\x00')
        f.write(b'\x00\x03\x93\xC9')
        f.write(b'\x00\x01')
        f.write(b'\x01')
        f.write(b'\x01')

        f.write(b'\x00\x03\x93\xB9')
        f.write(b'\x07\xD5\x0C\x0F\x11\x23\x13\x00\x00')
        f.write(b'\x00\xAB\xCD\x12\x35')
        f.write(b'\x01')
        f.write(b'\x3A\xAB\xCD\x12\x34') # -> 24
        f.write(b'\x01')
        f.write(b'\x78\xAB\x01')
        f.write(b'\x07')
        f.write(b'\x00')
        f.write(b'\x01')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x08')
        f.write(b'\x00')
        f.write(b'\x01')
        f.write(b'\x01\x77')
        f.write(b'\x02\x71')
        f.write(b'\x00\x03\x93\x87') # -> 26

        with open('annexc.data','rb') as g:
            f.write(g.read())
            
    with open('twofingers.fir','wb') as f:
        f.write(b'\x46\x49\x52\x00')
        f.write(b'\x30\x32\x30\x00')
        f.write(b'\x00\x01\xE8\xB4')
        f.write(b'\x00\x02')
        f.write(b'\x00')
        f.write(b'\x02')

        f.write(b'\x00\x00\xF4\x52')
        f.write(b'\x07\xD5\x0C\x0F\x11\x23\x13\x00\x00')
        f.write(b'\x00\xAB\xCD\x12\x35')
        f.write(b'\x01')
        f.write(b'\x3A\xAB\xCD\x12\x34')
        f.write(b'\x07')
        f.write(b'\x00')
        f.write(b'\x01')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x08')
        f.write(b'\x00')
        f.write(b'\x01')
        f.write(b'\x00\xFA')
        f.write(b'\x00\xFA')
        f.write(b'\x00\x00\xF4\x24') # -> 46

        with open('finger.data','rb') as g:
            f.write(g.read())
            
        f.write(b'\x00\x00\xF4\x52')
        f.write(b'\x07\xD5\x0C\x0F\x11\x23\x13\x00\x00')
        f.write(b'\x00\xAB\xCD\x12\x35')
        f.write(b'\x01')
        f.write(b'\x3A\xAB\xCD\x12\x34')
        f.write(b'\x08')
        f.write(b'\x01')
        f.write(b'\x01')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x01\xF4')
        f.write(b'\x08')
        f.write(b'\x00')
        f.write(b'\x01')
        f.write(b'\x00\xFA')
        f.write(b'\x00\xFA')
        f.write(b'\x00\x00\xF4\x24') # -> 46

        with open('finger.data','rb') as g:
            f.write(g.read())
            

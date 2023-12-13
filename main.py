import pudb; 
import tpdb
import pdb; 
# pudb.set_trace()
# pdb.set_trace()

var = 'Testing'

tpdb.set_trace()

def test():
    print("In a function")
    return True

with open('test_folder/test.txt', 'w') as fil:
    fil.write('It works!')
test()
print("Hello World")
print("Hello World")
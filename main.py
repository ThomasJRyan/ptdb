import pudb; 
import tpdb
import pdb; 
# pdb.set_trace()

var = 'Testing'
numvar = 10
listvar = [1,2,3]
dictvar = {'a': 1, 'b': 2, 'c': 3}
# pudb.set_trace()
tpdb.set_trace()

def test():
    print("In a function")
    return True

with open('test.txt', 'w') as fil:
    fil.write('It works!')
test()
print("Hello World")
print("Hello World")

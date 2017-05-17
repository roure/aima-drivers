from itertools import product


x = [0, 1, 2, 3, 4, 5]
y = [2, 4]
z = [item for item in x if item not in y]

def subs(x, y):
    return [item for item in x if item not in y]

for a, b in product([0,1,2], ['a','b','c']):
    print('{}, {}'.format(a,b))
print()
k = x[1:4]

print(x[0:3])

print(k)
x.insert(2,10)
print(k)
print(x)

print(z)

x = subs(x, y)
print(x)
import re
def parse(s):
    tok=re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
    st=[[]]
    for m in tok.finditer(s):
        t=m.group(0)
        if t=='(': st.append([])
        elif t==')': x=st.pop(); st[-1].append(x)
        else: st[-1].append(t[1:-1] if t[0]=='"' else t)
    return st[0][0]
def find(n,key):
    out=[]
    if isinstance(n,list):
        if n and n[0]==key: out.append(n)
        for c in n: out+=find(c,key)
    return out
